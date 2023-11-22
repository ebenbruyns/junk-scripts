#!/usr/bin/env python
import json
import argparse
import configparser
import os
import shutil
import sqlite3
import sys
import xml.etree.ElementTree as ET
import glob

import zipfile
import chardet
import subprocess

import database
cols = database.cols


def load_conf_data_from_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
        for section in data['Sections']:
            section['Name'] = section['Name'].lower()
            for option in section['Options']:
                option['Key'] = option['Key'].lower()
        return data


def fix_shortnames(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("update Game set ShortName = config_set.ShortName from  config_set where lower(Game.ShortName) = lower(config_set.ShortName)")
    conn.commit()
    conn.close()


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


def store_config_in_database(shortname, forkname, version, platform, sections, autoexec, db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    config_set_id = 0
    c.execute("select id from config_set where ShortName = ? AND forkname = ? AND version = ? AND platform = ?",
              (shortname, forkname, version, platform))
    row = c.fetchone()
    if row is None:
        c.execute("INSERT INTO config_set (ShortName, forkname, version, platform) VALUES (?, ?, ?, ?)",
                  (shortname, forkname, version, platform))
        config_set_id = c.lastrowid
    else:
        config_set_id = row[0]
        c.execute("DELETE FROM configs WHERE config_set_id = ?",
                  (config_set_id,))
    for section, settings in sections.items():
        for key, value in settings.items():
            value = value.replace('$', '$$')
            query = "INSERT INTO configs (section, key, value, config_set_id) VALUES (?, ?, ?, ?)"
            params = (section, key, value, config_set_id)
            c.execute(query, params)
    autoexec = autoexec.replace('$', '$$')
    query = "INSERT INTO configs (section, key, value, config_set_id) VALUES (?, ?, ?, ?)"
    params = ('autoexec', 'text', autoexec, config_set_id)
    c.execute(query, params)
    conn.commit()
    conn.close()


def find_section(config_data, section_name):
    for section in config_data['Sections']:
        if section['Name'] == section_name:
            return section
    return None


def find_option(section, key):
    for option in section['Options']:
        if option['Key'] == key:
            return option
    return None


def parse_metadata_file(xml_file, db_file):
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        conn = None
    c = conn.cursor()
    conn.commit()
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for game in root.findall("./Game"):
        try:
            title = game.find("Title").text
            if not title:
                continue
            vals = []
            shortname = ""
            for node in cols:
                val_node = game.find(node)
                if val_node is None:
                    val = ""
                else:
                    val = val_node.text
                if node == "RootFolder":
                    root_folder = val_node.text
                    if "\\" in root_folder:
                        short_name = root_folder.split("\\")[-1]
                    else:
                        short_name = root_folder.split("/")[-1]

                if (val is str):
                    vals.append(val.replace("'", "''"))
                else:
                    vals.append(val)
            vals.append("")
            vals.append(short_name.lower())

            placeholders = ', '.join(['?' for _ in range(len(cols) + 1)])
            cols_with_pk = cols + ["SteamClientID", "ShortName"]
            placeholders = ', '.join(['?' for _ in range(len(cols_with_pk))])
            tmp = f"INSERT INTO Game ({', '.join(cols_with_pk)}) VALUES ({placeholders})"
            c.execute(tmp, vals)

            conn.commit()
        except Exception as e:
            print(f"Error parsing metadata for game: {title} {e}")
    conn.close()


def parse_file(directory, forkname, version, platform, config_file, dbfile):
    if not os.path.exists(config_file):
        return
    sections, autoexec_text = parse_config_file(config_file)
    ShortName = os.path.basename(os.path.normpath(directory))
    store_config_in_database(
        ShortName, forkname, version, platform, sections, autoexec_text, dbfile)


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


def find_image_files(base_dir, dirs, title):
    files = []
    for d in dirs:
        path = os.path.join(base_dir, d)
        for f in os.listdir(path):
            lower_title = title.lower()
            for ch in ['/', '\\', ':', '?', '"', '<', '>', '|', '*', "'"]:
                lower_title = lower_title.replace(ch, "_")
            if f.lower().startswith(lower_title+'-') and (f.endswith('.jpg') or f.endswith('.png') or f.endswith('.gif') or f.endswith('.jpeg') or
                                                          f.endswith('.bmp') or f.endswith('.tiff') or f.endswith('.tif')):
                files.append(os.path.join(d, f))
    return files


def get_zip_files_in_dir(base_dir):
    base_dir = os.path.abspath(base_dir)
    zip_files = glob.glob(f"{base_dir}/*.zip")
    return [os.path.basename(file) for file in zip_files]


def get_file_from_path(path: str):
    if (path != None):
        parts = path.split("\\")
        return parts[len(parts) - 1].replace(".bat", ".zip")
    return ""


def find_all_game_zips(db_file, base_dir):
    zipFiles = get_zip_files_in_dir(base_dir)
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT ID, ShortName, Title, ApplicationPath FROM Game")
    games = c.fetchall()

    for game in games:
        game_id = game[0]
        shortname = game[1]
        title = game[2]
        application_path = game[3]
        game_zip = get_file_from_path(application_path)
        if game_zip != "":
            found = False
            for zipFile in zipFiles:
                if zipFile.lower() == game_zip.lower():
                    c.execute(
                        "INSERT INTO ZipFiles (GameID, ZipFileName) VALUES (?, ?)", (game_id, zipFile))
                    found = True
            if not found:
                print(f"Game zip {game_zip} not found")
    conn.commit()
    conn.close()


def find_all_bat_files(db_file, base_dir, temp_dir):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("""SELECT Game.ID, Game.ShortName, Game.Title, ZipFiles.ZipFileName FROM Game  
              LEFT JOIN ZipFiles  ON game.ID = ZipFiles.GameID JOIN Config_Set ON Game.ShortName = config_set.ShortName WHERE config_set.platform = 'linux'""")
    games = c.fetchall()

    for game in games:
        game_id = game[0]
        shortname = game[1]
        title = game[2]
        zip_file_name = game[3]
        game_zip = os.path.expanduser(os.path.join(base_dir, zip_file_name))
        with zipfile.ZipFile(game_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        bat_files = []
        for root, subdirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith("run.bat") or file.lower().endswith("runme.bat") or file.lower().endswith("network.bat"):
                    bat_files.append(os.path.join(root, file))
        for bat_file in bat_files:
            print(f"found {bat_file}")
            with open(bat_file, 'rb') as f:
                result = chardet.detect(f.read())
                encoding = result['encoding']

            with open(bat_file, 'r', encoding=encoding) as f:
                content = f.read()
                # remove temp_dir from path
                bat_file = bat_file.replace(temp_dir, "")
                print(f"Inserting {bat_file}")
                c.execute(
                    "INSERT INTO BatFiles (GameID, Path, BatFileName, Content) VALUES (?, ?, ?, ?)", (game_id, bat_file, os.path.basename(bat_file), content))
        shutil.rmtree(temp_dir)

        conn.commit()
    conn.close()


def patch_bat_files(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("""select id, GameId, Path, content from batfiles""")
    rows = c.fetchall()
    for row in rows:
        id = row[0]
        gameId = row[1]
        path = row[2]

        content = row[3]
        content = content.replace(".\\eXoDOS\\", ".\\")
        content = content.replace(".\\eXoWin3x\\", ".\\")
        content = content.replace("./eXoDOS/", "./")
        content = content.replace("./eXoWin3x/", "./")
        content = content.replace(
            "IPXNET CONNECT %IP%", "IPXNET CONNECT %IP% 1213")
        content = content.replace(
            "ipxnet startserver", "ipxnet startserver 1213")
        c.execute("update batfiles set content = ? where id = ?",
                  (content, id))
    conn.commit()
    conn.close()


def find_image_files(base_dir):
    cmd = f"find \"{base_dir}\" -type f -print"
    output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                              shell=True, env=os.environ).communicate()[0].decode().split('\n')
    result = []
    for line in output:
        if line.endswith('.jpg') or line.endswith('.png') or line.endswith('.gif') or line.endswith('.jpeg') or line.endswith('.bmp') or line.endswith('.tiff') or line.endswith('.tif'):
            result.append(line)
    return result


def find_and_store_images(db_file, base_dir):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT ID, ShortName, Title FROM Game")
    games = c.fetchall()
    all_images = find_image_files(base_dir)
    for image in all_images:
        file_name = os.path.basename(image)
        # print(f"Inserting {image}")
        c.execute("INSERT INTO Images (ImagePath, FileName, SortOrder) VALUES (?, ?, 999)",
                  (image.replace(os.path.expanduser(base_dir)+'/', ""), file_name.lower(),))
    conn.commit()

    for game in games:
        game_id = game[0]
        shortname = game[1]
        title = game[2]
        illigal_file_chars = ['/', '\\', ':',
                              '?', '"', '<', '>', '|', '*', '\'']
        safe_name = title
        for ch in illigal_file_chars:
            safe_name = safe_name.replace(ch, "_")
        safe_name = safe_name.lower()
        safe_name += '-%'
        # print(f"Updating {safe_name}")
        c.execute(f"update images set GameID = ? where FileName like '{safe_name}'",
                  (game_id,))
    sorted_order = ["Box - Front", "Box - Front - Reconstructed", "Fanart - Box - Front", "Cart - Front",
                    "Screenshot - Game Title", "Screenshot - Gameplay", "Disc"]
    i = 0
    for s in sorted_order:
        i += 1
        c.execute(
            f"update images set SortOrder = {i} where ImagePath like '{s}%'")
    conn.commit()
    conn.close()


def read_json_from_stdin():
    json_str = sys.stdin.read()
    json_obj = json.loads(json_str)
    return json_obj


def fix_auto_exec(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(
        "select id, value from configs where section = 'autoexec' and key = 'text'")
    rows = c.fetchall()
    for row in rows:
        id = row[0]
        value = row[1]
        newValue = value
        newValue = newValue.replace(".\\eXoDOS\\", ".\\")
        newValue = newValue.replace(".\\eXoWin3x\\", ".\\")
        newValue = newValue.replace("./eXoDOS/", "./")
        newValue = newValue.replace("./eXoWin3x/", "./")
        if (newValue != value):
            c.execute("update configs set value = ? where id = ?",
                      (newValue, id))
            conn.commit()
    conn.close()


def fix_win_auto_exec(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(
        "select id, value from configs where section = 'autoexec' and key = 'text'")
    rows = c.fetchall()
    for row in rows:
        id = row[0]
        value = row[1]

        newvalue = value.replace(".\\eXoWin3x\\", ".\\")
        if (newvalue != value):
            c.execute("update configs set value = ? where id = ?",
                      (newvalue, id))
            conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--parsefile', nargs=2, help='Path to the DOSBox configuration file filename and shortname'
    )
    parser.add_argument(
        '--parsejson', help='Configuration shortname, the json is read from stdin'
    )
    parser.add_argument(
        '--parsedir', help='Base directory for DOSBox configuration files')

    parser.add_argument(
        '--parsemetadata', help='Path to the MS-DOS META-DATA file')
    parser.add_argument(
        '--dbfile', help='Path to the SQLite database file', default='configs.db')
    parser.add_argument(
        '--fixshortnames', help='Fix shortnames in the database', action='store_true')
    parser.add_argument(
        '--platform', help='Platform [windows,linux]', default='linux')
    parser.add_argument(
        '--forkname', help='dosbox fork name', default='')
    parser.add_argument(
        '--version', help='dosbox version', default='')
    parser.add_argument(
        '--findimages', help='Find and store images')

    parser.add_argument(
        '--findallgamezips', help='Find all game zips'
    )

    parser.add_argument(
        '--fixautoexec', help='Fix autoexec', action='store_true'
    )
    parser.add_argument(
        '--fixwinautoexec', help='Fix win autoexec', action='store_true'
    )
    parser.add_argument(
        '--extractbatfiles', nargs=2, help='Get all bat files'
    )
    parser.add_argument(
        '--patchbatfiles', help='Patch bat files', action='store_true'
    )

    args = parser.parse_args()
    database.create_tables(args.dbfile)
    if args.parsefile:
        parse_file(args.parsefile[0], args.forkname,
                   args.version, args.platform, args.parsefile[1], args.dbfile)
    if args.parsedir:
        for directory in os.listdir(args.parsedir):
            if not os.path.isdir(os.path.join(args.parsedir, directory)):
                continue
            config_file = os.path.join(
                args.parsedir, directory, 'dosbox_linux.conf')
            parse_file(directory, args.forkname, args.version,
                       'linux', config_file, args.dbfile)
            config_file = os.path.join(
                args.parsedir, directory, 'dosbox.conf')
            parse_file(directory, args.forkname, args.version,
                       'windows', config_file, args.dbfile)
    if args.parsemetadata:
        parse_metadata_file(args.parsemetadata, args.dbfile)
    if args.fixshortnames:
        fix_shortnames(args.dbfile)
    if args.findimages:
        find_and_store_images(args.dbfile, args.findimages)

    if args.findallgamezips:
        find_all_game_zips(args.dbfile, args.findallgamezips)

    if args.fixautoexec:
        fix_auto_exec(args.dbfile)
    if args.fixwinautoexec:
        fix_win_auto_exec(args.dbfile)
    if args.extractbatfiles:
        find_all_bat_files(
            args.dbfile, args.extractbatfiles[0], args.extractbatfiles[1])
    if args.patchbatfiles:
        patch_bat_files(args.dbfile)

    if not any(vars(args).values()):
        parser.print_help()


if __name__ == '__main__':
    main()
