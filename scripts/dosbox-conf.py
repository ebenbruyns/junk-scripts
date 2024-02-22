#!/usr/bin/env python
import re
import time
import json
import argparse
import configparser
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET
from typing import List
import database
import urllib.parse

cols = database.cols


def parse_config_file(filepath):
    try:
        with open(filepath, 'r') as f:
            text = f.read()
            autoexec_start = text.find('[autoexec]')
            if autoexec_start != -1:
                config_text = text[:autoexec_start]
                autoexec_text = text[autoexec_start + len('[autoexec]'):]
            else:
                config_text = text
                autoexec_text = ''
            config = configparser.ConfigParser()
            config.read_string(config_text)
            sections = {}
            for section in config.sections():
                settings = {}
                for key, value in config.items(section):
                    settings[key] = value
                sections[section] = settings
            return sections, autoexec_text
    except Exception as e:
        print(f"Error parsing config file: {filepath} {e}")
        return None, None


def get_config(shortnames, forkname, version, platform, db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    config = configparser.ConfigParser()
    autoexec_text = ""
    id = 0
    for shortname in shortnames:
        c.execute("""SELECT config_set.id from config_Set
                WHERE config_set.ShortName = ? AND (config_set.forkname = '' or config_set.forkname = ?) AND 
                (config_set.version = '' or config_set.version = ?) AND 
                (config_set.platform = '' or config_set.platform = ?)
                order by config_set.platform desc, config_set.forkname desc, config_set.version desc""", (shortname, forkname, version, platform))
        row = c.fetchone()
        id = row[0]
        c.execute(
            """SELECT config_set.ShortName, configs.section, configs.key, configs.value FROM configs 
            JOIN config_set ON configs.config_set_id = config_set.id 
            WHERE config_set.id = ? AND 
            configs.section != 'autoexec'""", (id,))
        for row in c.fetchall():
            _, section, key, value = row

            if not config.has_section(section):
                config.add_section(section)
            config.set(section, key, value)
        c.execute(
            """SELECT value FROM configs JOIN config_set ON configs.config_set_id = config_set.id 
            WHERE config_set.id = ? AND 
            configs.section = 'autoexec' AND configs.key = 'text'""", (id,))
        row = c.fetchone()
        if row is not None:
            autoexec_text += row[0]
    config.write(open('dosbox.conf', 'w'))
    with open('dosbox.conf', 'w') as f:
        config.write(f)
        f.write('[autoexec]')
        f.write(autoexec_text)
    conn.close()


def update_bat_files(db_file, shortname, batfiles):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    for batfile in batfiles:
        c.execute("select id from Game where ShortName = ?", (shortname,))
        row = c.fetchone()
        if row is not None:
            game_id = row[0]
            c.execute("select id from BatFiles where GameID = ? AND Path = ?",
                      (game_id, batfile['Path']))
            row = c.fetchone()
            if row is None:
                c.execute("INSERT INTO BatFiles (GameID, Path, BatFileName, Content) VALUES (?, ?, ?, ?)",
                          (game_id, batfile['Path'], batfile['BatFileName'], batfile['Content']))
            else:
                c.execute("UPDATE BatFiles SET Content = ? WHERE id = ?",
                          (batfile['Content'], row[0]))
    conn.commit()
    conn.close()
    return json.dumps({'Type': 'Success', 'Content': {'success': True}})


def lookup_title(shortname, db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT Title FROM Game WHERE ShortName=?", (shortname,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None


def get_file_from_path(path: str):
    if (path != None):
        parts = path.split("\\")
        return parts[len(parts) - 1].replace(".bat", ".zip")
    return ""


def write_bat_files(db_file, shortname):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("""select id, GameId, Path, content from batfiles where GameId = (select id from game where shortname = ?)""", (shortname,))
    rows = c.fetchall()
    for row in rows:
        id = row[0]
        gameId = row[1]
        path = row[2]
        content = row[3]
        dir = os.path.dirname(path)
        print(f"Writing {dir}")
        print(f"Writing {path}")
        print(f"Content {content}")
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(path, 'w') as f:
            f.write(content)


def get_json_bat_files(db_file, shortname):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("""select id, GameId, Path, content from batfiles where GameId = (select id from game where shortname = ?)""", (shortname,))
    rows = c.fetchall()
    result = []
    for row in rows:
        id = row[0]
        gameId = row[1]
        path = row[2]
        content = row[3]
        result.append({'Id': id, 'GameId': gameId,
                      'Path': path, 'Content': content})
    return json.dumps({'Type': 'FileContent', 'Content': {'Files': result}})


def display_game_details(game_data):
    html = f"<div style=' width: 100%;'>"
    html += f"<p style='width:100%; white-space: pre-wrap;'>{game_data['Description']}</p>"
    html += f"</div>"
    html += f"<div>"
    html += f"<p>Publisher: {game_data['Publisher']}</p>"
    html += f"<p>Developer: {game_data['Developer']}</p>"
    html += f"<p>Genre: {game_data['Genre']}</p>"
    html += f"<p>Release Date: {game_data['ReleaseDate']}</p>"
    html += f"</div>"
    return html


def get_editors(db_file, shortname):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT ID FROM Game WHERE ShortName=?", (shortname,))
    game_id = c.fetchone()[0]
    editors = []
    # if game_id:
    #     editors = [{'Type': 'IniEditor',
    #                 'InitActionId': 'GetRunnerConfigActions',
    #                 'Title': 'Runner',
    #                 'Description': 'Configures the runner to use with the launcher',
    #                 'ContentId': shortname}]
    c.execute("SELECT ID FROM Config_Set WHERE ShortName=?", (shortname,))
    config_set_id = c.fetchone()
    if config_set_id:
        editors = editors + [{'Type': 'IniEditor',
                              'InitActionId': 'GetDosboxConfigFileActions',
                              'Description': 'Configures the dosbox.conf file for the game',
                              'Title': 'Dosbox.config',
                              'ContentId': shortname}]

    c.execute("SELECT ID FROM BatFiles WHERE GameID=?", (game_id,))
    bat_files = c.fetchone()
    if bat_files:
        editors = editors + [{'Type': 'FileEditor',
                              'InitActionId': 'GetBatFileActions',
                              'Description': 'Edit the bat files for the game',
                              'Title': 'Bat Files',
                              'ContentId': shortname}]
    conn.close()

    return editors


def get_game_data(db_file, shortname, image_prefix, urlencode):
    conn = sqlite3.connect(db_file)

    c = conn.cursor()

    c.execute(
        f"SELECT {', '.join([f'{col} TEXT' for col in cols])} , SteamClientID FROM Game WHERE ShortName=? ", (shortname,))

    result = c.fetchone()

    if result:
        releseDate = result[11]
        if releseDate:
            releseDate = releseDate.split("-")[0]
        game_data = {
            'Name': result[0],
            'Description': result[1],
            'ApplicationPath': result[2],
            'ManualPath': result[3],
            'Publisher': result[4],
            'RootFolder': result[5],
            'Source': result[6],
            'DatabaseID': result[7],
            'Genre': result[8],
            'ConfigurationPath': result[9],
            'Developer': result[10],
            'ReleaseDate': releseDate,
            'SteamClientID': result[12],
            'ShortName': shortname,
            'HasDosConfig': False,
            'HasBatFiles': False,
        }

        c.execute("SELECT ID FROM Game WHERE ShortName=?", (shortname,))
        game_id = c.fetchone()

        image_files = []
        c.execute(
            "SELECT ImagePath FROM Images join Game on Game.ID = Images.GameID WHERE ShortName=? order by Images.SortOrder", (shortname,))
        images = c.fetchall()
        for image in images:
            image_path = image[0]
            if (image_path == None):
                image_url = ""
            else:
                if (urlencode):
                    image_path = urllib.parse.quote(image_path)
                image_url = image_prefix + image_path
            image_files.append(image_url)

        conn.close()
        result = {
            'Name': result[0],
            'Description': display_game_details(game_data),
            'ApplicationPath': result[2],
            'ManualPath': result[3],
            'RootFolder': result[5],
            'ConfigurationPath': result[9],
            'SteamClientID': result[12],
            'ShortName': shortname,
            'HasDosConfig': False,
            'HasBatFiles': False,
            'Editors': get_editors(db_file, shortname)
        }
        result['Images'] = image_files
        return json.dumps({'Type': 'GameDetails', 'Content':  result})
    else:
        return None


def get_games_with_images(db_file, image_prefix, filter_str, installed, isLimited, urlencode, needsLogin):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    limited_clause = ""
    if (isLimited.lower() == "true"):
        limited_clause = "LIMIT 100"
    if (installed.lower() == "true"):
        c.execute(
            f"SELECT Game.ID, ShortName, Title, SteamClientID FROM Game WHERE SteamClientID <> '' and LOWER(Title) LIKE ? ORDER BY Title {limited_clause}", ('%' + filter_str.lower().replace(" ", "%") + '%',))
    else:
        c.execute(
            f"SELECT Game.ID, ShortName, Title, SteamClientID FROM Game WHERE LOWER(Title) LIKE ? ORDER BY Title {limited_clause}", ('%' + filter_str.lower().replace(" ", "%") + '%',))
    games = c.fetchall()
    result = []
    for game in games:
        game_id = game[0]
        shortname = game[1]
        title = game[2]
        steam_client_id = game[3]
        c.execute(
            "SELECT ImagePath FROM Images WHERE GameID=? order by SortOrder", (game_id,))
        images = c.fetchall()
        image_files = []
        for image in images:
            image_path = image[0]
            if (image_path == None):
                image_url = ""
            else:
                if (urlencode):
                    image_path = urllib.parse.quote(image_path)

                image_url = image_prefix + image_path
            image_files.append(image_url)
        result.append({'ID': game_id, 'Name': title,
                      'Images': image_files, 'ShortName': shortname, 'SteamClientID': steam_client_id})
    conn.close()
    return json.dumps({'Type': 'GameGrid', 'Content':  {'NeedsLogin': needsLogin, 'Games': result}})


def read_json_from_stdin():
    json_str = sys.stdin.read()
    json_obj = json.loads(json_str)
    return json_obj


def add_steam_client_id(shortname, steam_client_id, db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("UPDATE Game SET SteamClientID=? WHERE ShortName=?",
              (steam_client_id, shortname))
    conn.commit()
    conn.close()


def clear_steam_client_id(shortname, db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("UPDATE Game SET SteamClientID='' WHERE ShortName=?",
              (shortname,))
    conn.commit()
    conn.close()


def get_zip_for_shortname(shortname, db_file, urlencode):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT ZipFileName FROM ZipFiles JOIN Game on Game.ID = ZipFiles.GameID WHERE ShortName=?", (shortname,))
    result = c.fetchone()
    conn.close()
    if result:
        if (urlencode):
            return urllib.parse.quote(result[0])
        return result[0]
    else:
        return None


def get_lauch_options(options, db_file):
    return json.dumps(
        {
            'Type': 'LaunchOptions',
            'Content':
            {
                'Exe': options[0],
                'Options': options[1],
                'WorkingDir': options[2],
                'Name': options[3]
            }
        })


def get_last_progress_update(file_path):
    progress_re = re.compile(
        r"([\d\.]+)([M|K|G])[ \.]*(\d+)% *([\d\.]+)([M|K|G])[ =]")
    size_re = re.compile(r"Length.*\(([\d\.]+)([M|K|G])\)")
    # The file is already fully retrieved; nothing to do.
    completed_re = re.compile(
        r"The file is already fully retrieved; nothing to do.")

    last_progress_update = None
    total_size = None

    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

            for line in lines:
                completed_match = completed_re.search(line)
                if completed_match:
                    last_progress_update = {
                        "Percentage": 100,
                        "Description": "Download Completed"
                    }
                    break

                size_match = size_re.search(line)
                if size_match:
                    total_size = float(size_match.group(1))  # Convert to KB
                    if size_match.group(2) == "G":
                        total_size = float(total_size) * 1024
                    elif size_match.group(2) == "K":
                        total_size = float(total_size) / 1024

                    break
            for line in reversed(lines):
                progress_match = progress_re.search(line)
                if progress_match and total_size is not None:
                    progress_current = int(progress_match.group(1))
                    if progress_match.group(2) == "G":
                        progress_current = float(progress_current) * 1024
                    elif progress_match.group(2) == "K":
                        progress_current = float(progress_current) / 1024
                    progress_percentage = int(progress_match.group(3))
                    download_speed_mb_per_sec = float(progress_match.group(4))

                    if progress_match.group(5) == "G":
                        download_speed_mb_per_sec = float(
                            download_speed_mb_per_sec) * 1024
                    elif progress_match.group(5) == "K":
                        download_speed_mb_per_sec = float(
                            download_speed_mb_per_sec) / 1024
                    else:
                        download_speed_mb_per_sec = float(
                            download_speed_mb_per_sec)
                    last_progress_update = {
                        "Percentage": progress_percentage,
                        "Description": "Downloaded " + str(round((progress_current), 2)) + " MB of " + str(round(total_size, 2)) + " MB (" + str(progress_percentage) + "%)\nSpeed: " + str(round(download_speed_mb_per_sec, 3)) + " MB/s"
                    }
                    break

    except Exception as e:
        print("Waiting for progress update", e, file=sys.stderr)
        time.sleep(1)

    return json.dumps({'Type': 'ProgressUpdate', 'Content': last_progress_update})


def get_setting(db_file, name):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT value FROM Settings WHERE name=?", (name,))
    result = c.fetchone()
    conn.close()
    if result:
        return json.dumps({'Type': 'Setting', 'Content': {'name': name, 'value': result[0]}})
    else:
        return json.dumps({'Type': 'Setting', 'Content': {'name': name, 'value': ''}})


def save_setting(db_file, name, value):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM Settings WHERE name=?",
              (name,))
    result = c.fetchone()
    if result[0] == 0:
        c.execute("INSERT INTO Settings (name, value) VALUES (?, ?)",
                  (name, value))
    else:
        c.execute("UPDATE Settings SET value=? WHERE name=?",
                  (value, name))
    conn.commit()
    conn.close()
    return json.dumps({'Type': 'Success', 'Content': {'success': True}})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--parsejson', help='Configuration shortname, the json is read from stdin'
    )
    parser.add_argument(
        '--updatebats', help='Update bat files')
    parser.add_argument(
        '--conf', nargs='+', help='List of shortnames to reproduce configuration file from database')
    parser.add_argument(
        '--confjson', nargs='+', help='List of shortnames to reproduce configuration file from database'
    )
    parser.add_argument(
        '--dbfile', help='Path to the SQLite database file', default='configs.db')
    parser.add_argument(
        '--platform', help='Platform [windows,linux]', default='linux')
    parser.add_argument(
        '--forkname', help='dosbox fork name', default='')
    parser.add_argument(
        '--version', help='dosbox version', default='')
    parser.add_argument(
        '--getgameswithimages', nargs='+', help='Get games with images')
    parser.add_argument(
        '--getgamedata', nargs=2, help='Get game data')
    parser.add_argument(
        '--addsteamclientid', nargs=2, help='Add steam client id to game')
    parser.add_argument(
        '--clearsteamclientid', nargs=1, help='Clear steam client id to game'
    )
    parser.add_argument(
        '--getzip', help='Get zip file for shortname'
    )
    parser.add_argument(
        '--launchoptions', nargs=4, help='Launch options'
    )
    parser.add_argument(
        '--writebatfiles', help='Write bat files'
    )
    parser.add_argument(
        '--getjsonbats', help='Get bat files as json'
    )
    parser.add_argument(
        '--getprogress', help='Get installtion progress for game')
    parser.add_argument(
        '--urlencode', help='Url encode string', action='store_true')
    parser.add_argument(
        '--getsetting', help='Get setting'
    )
    parser.add_argument(
        '--savesetting', nargs=2, help='Save setting'
    )

    args = parser.parse_args()
    database.create_tables(args.dbfile)
    if args.parsejson:
        config_data = read_json_from_stdin()
        print(database.parse_json_store_in_database(
            args.parsejson, args.forkname, args.version, args.platform, config_data, args.dbfile))
    if args.updatebats:
        batfiles = read_json_from_stdin()
        print(update_bat_files(args.dbfile, args.updatebats, batfiles))
    if args.conf:
        get_config(
            args.conf, args.forkname, args.version, args.platform, args.dbfile)
    if args.confjson:
        print(database.get_config_json(
            args.confjson, args.forkname, args.version, args.platform, args.dbfile))
    if args.getgameswithimages:
        filter = ""
        urlencode = False
        if (args.urlencode):
            urlencode = True
        if (len(args.getgameswithimages) > 1):
            filter = args.getgameswithimages[1]
            installed = args.getgameswithimages[2]
            isLimited = args.getgameswithimages[3]
            needsLogin = args.getgameswithimages[4]
        print(get_games_with_images(args.dbfile,
              args.getgameswithimages[0], filter, installed, isLimited, urlencode, needsLogin))
    if args.getgamedata:
        urlencode = False
        if (args.urlencode):
            urlencode = True
        print(get_game_data(args.dbfile,
              args.getgamedata[0], args.getgamedata[1], urlencode))
    if args.addsteamclientid:
        add_steam_client_id(
            args.addsteamclientid[0], args.addsteamclientid[1], args.dbfile)
        print(json.dumps({'Type': 'Success', 'Content': {'success': True}}))
    if args.clearsteamclientid:
        clear_steam_client_id(args.clearsteamclientid[0], args.dbfile)
        print(json.dumps({'Type': 'Success', 'Content': {'success': True}}))
    if args.getzip:
        urlencode = False
        if (args.urlencode):
            urlencode = True
        print(get_zip_for_shortname(args.getzip, args.dbfile, urlencode))
    if args.launchoptions:
        print(get_lauch_options(args.launchoptions, args.dbfile))
    if args.writebatfiles:
        write_bat_files(args.dbfile, args.writebatfiles)
    if args.getjsonbats:
        print(get_json_bat_files(args.dbfile, args.getjsonbats))
    if args.getprogress:
        print(get_last_progress_update(args.getprogress))
    if args.getsetting:
        print(get_setting(args.dbfile, args.getsetting))
    if args.savesetting:
        print(save_setting(args.dbfile,
              args.savesetting[0], args.savesetting[1]))
    if not any(vars(args).values()):
        parser.print_help()


if __name__ == '__main__':
    main()
