#!/usr/bin/env python
import re
import time
import json
import argparse
import configparser
import os
import shutil
import sqlite3
import sys
import xml.etree.ElementTree as ET
import glob

from typing import List
import zipfile
import chardet
import subprocess

import database
import urllib.parse
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


def get_config_json(shortnames, forkname, version, platform, db_file):
    config_data = load_conf_data_from_json(os.path.expanduser(
        '~/homebrew/plugins/Junk-Store/staging_conf.json'))
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    autoexec_text = ""
    id = 0
    parent_name = "default"
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
            section = find_section(config_data, section)
            if section is not None:
                option = find_option(section, key)
                if option is not None:
                    if parent_name != "default":
                        option['Parents'] = [
                            {'Parent': parent_name, 'Value': value}] + option['Parents']
                    option['Value'] = value
        c.execute(
            """SELECT value FROM configs JOIN config_set ON configs.config_set_id = config_set.id 
            WHERE config_set.id = ? AND 
            configs.section = 'autoexec' AND configs.key = 'text'""", (id,))
        row = c.fetchone()
        if row is not None:
            autoexec_text += row[0]
        parent_name = shortname
    config_data['Autoexec'] = autoexec_text
    conn.close()
    return json.dumps(config_data)


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


def parse_json_store_in_database(shortname, forkname, version, platform, config_data, db_file):
    # filename = os.path.expanduser(f"~/{shortname}_{platform}_{forkname}.json")
    # with open(filename, 'w') as f:
    #     json.dump(config_data, f)
    conn = sqlite3.connect(db_file)
    print(
        f"Shortname: {shortname} Forkname: {forkname} Version: {version} Platform: {platform}")
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
    for section in config_data['Sections']:
        for option in section['Options']:
            value = option['Value']
            value = value.replace('$', '$$')
            shouldUpdate = True
            if (option['Value'] == option['DefaultValue']):
                shouldUpdate = False

            if (option['Parents'] and len(option['Parents']) > 0 and option['Parents'][0]['Value'] == option['Value']
                    and option['Parents'][0]['Parent'] != 'default'):
                shouldUpdate = False
            if (shouldUpdate):
                query = "INSERT INTO configs (section, key, value, config_set_id) VALUES (?, ?, ?, ?)"
                params = (section['Name'], option['Key'], value, config_set_id)
                print(f"Inserting {params}")
                c.execute(query, params)
                conn.commit()
    autoexec = config_data['Autoexec']
    autoexec = autoexec.replace('$', '$$')
    query = "INSERT INTO configs (section, key, value, config_set_id) VALUES (?, ?, ?, ?)"
    params = ('autoexec', 'text', autoexec, config_set_id)
    c.execute(query, params)
    conn.commit()
    conn.close()


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

# sample menu
#
# 1 Command & Conquer: Red Alert Allied Campaign
# 2 Command & Conquer: Red Alert Soviet Campaign
# 3 Command & Conquer: Red Alert Aftermath
# 4 Command & Conquer: Red Alert Counter Strike
# 5 Network Multiplayer
# 6 Quit
#
#  This game contains 4 discs. The choice above loads the required
#  disc for that campaign. If you attempt to start a different
#  campaign than the one you select here, you will have to hit
#  ctrl-f4 to switch through the mounted CD's until you find the
#  right one.
#
#  To play the hidden campaign, choose Counterstrike and hold
#  SHIFT while clicking on the speaker on the main menu.
#
# sample bat file 1
# :menu
# @echo off
# cls
# echo.
# echo Press 1 for Command & Conquer: Red Alert Allied Campaign
# echo Press 2 for Command & Conquer: Red Alert Soviet Campaign
# echo Press 3 for Command & Conquer: Red Alert Aftermath
# echo Press 4 for Command & Conquer: Red Alert Counter Strike
# echo Press 5 for Network Multiplayer
# echo Press 6 to Quit
# echo.
# echo This game contains 4 discs. The choice above loads the required
# echo disc for that campaign. If you attempt to start a different
# echo campaign than the one you select here, you will have to hit
# echo ctrl-f4 to switch through the mounted CD's until you find the
# echo right one.
# echo.
# echo To play the hidden campaign, choose Counterstrike and hold
# echo SHIFT while clicking on the speaker on the main menu.
# echo.
# choice /C:123456 /N Please Choose:

# if errorlevel = 6 goto quit
# if errorlevel = 5 goto network
# if errorlevel = 4 goto CS
# if errorlevel = 3 goto AM
# if errorlevel = 2 goto RAS
# if errorlevel = 1 goto RAA

# :RAA
# @imgmount d ".\comconra\cd\Red Alert CD1.iso" ".\comconra\cd\Red Alert CD2.iso" ".\comconra\cd\Red Alert Counterstrike CD3.cue" ".\comconra\cd\Red Alert Aftermath CD4.cue" -t iso
# cd redalert
# cls
# @ra
# goto quit

# :RAS
# @imgmount d ".\comconra\cd\Red Alert CD2.iso" ".\comconra\cd\Red Alert CD1.iso" ".\comconra\cd\Red Alert Counterstrike CD3.cue" ".\comconra\cd\Red Alert Aftermath CD4.cue" -t cdrom
# cd redalert
# cls
# @ra
# goto quit

# :AM
# @imgmount d ".\comconra\cd\Red Alert Aftermath CD4.cue" ".\comconra\cd\Red Alert CD1.iso" ".\comconra\cd\Red Alert CD2.iso" ".\comconra\cd\Red Alert Counterstrike CD3.cue" -t cdrom
# cd redalert
# cls
# @ra
# goto quit

# :CS
# @imgmount d ".\comconra\cd\Red Alert Counterstrike CD3.cue" ".\comconra\cd\Red Alert CD1.iso" ".\comconra\cd\Red Alert CD2.iso" ".\comconra\cd\Red Alert Aftermath CD4.cue" -t cdrom
# cd redalert
# cls
# @ra
# goto quit

# :network
# @imgmount d ".\comconra\cd\Red Alert Aftermath CD4.cue" -t cdrom
# cls
# network

# :quit
# rem exit

# sample menu 2
#
# a Marco Polo
# b Westward HO!
# c The Longest Automobile Race
# d The Orient Express
# e Amelia Earhart: Around the World Flight
# f Tour de France
# g Appalachian Trail
# h Subway Scavenger
# i Hong Kong Hustle
# j Voyage to Neptune
# k Quit
#

# sample bat file 2
# @echo off
# cls
# echo.
# echo Press A for Marco Polo
# echo Press B for Westward HO!
# echo Press C for The Longest Automobile Race
# echo Press D for The Orient Express
# echo Press E for Amelia Earhart: Around the World Flight
# echo Press F for Tour de France
# echo Press G for Appalachian Trail
# echo Press H for Subway Scavenger
# echo Press I for Hong Kong Hustle
# echo Press J for Voyage to Neptune
# echo Press K to Quit
# echo.
# choice /C:ABCDEFGHIJK /N Please Choose:

# if errorlevel = 11 goto end
# if errorlevel = 10 goto nept
# if errorlevel = 9 goto hong
# if errorlevel = 8 goto subway
# if errorlevel = 7 goto trail
# if errorlevel = 6 goto tour
# if errorlevel = 5 goto amelia
# if errorlevel = 4 goto orient
# if errorlevel = 3 goto auto
# if errorlevel = 2 goto west
# if errorlevel = 1 goto marco

# :marco
# cls
# @call marco.bat
# goto menu

# :west
# cls
# @call WESTHO.bat
# goto menu

# :auto
# cls
# @call AUTORACE.bat
# goto menu

# :orient
# cls
# @call ORIENT.bat
# goto menu


# :amelia
# cls
# @call EARHART.bat
# goto menu


# :tour
# cls
# @call TOUR.bat
# goto menu


# :trail
# cls
# @call APP.bat
# goto menu


# :subway
# cls
# @call SUBWAY.bat
# goto menu


# :hong
# cls
# @call HONGKONG.bat
# goto menu


# :nept
# cls
# @call NEPTUNE.bat
# goto menu

# :end

# do not alter this with menu.exe

# sample bat file 3
# :menu
# @echo off
# cls
# echo.
# echo Please choose which map you would like to try:
# echo.
# echo A - Abstractions     I - Flooded          Q - Office Hell
# echo B - Arena            J - Fountain         R - Penta
# echo C - Army Arena       K - Gauntlet         S - Spiral
# echo D - Battle at Home   L - Mandyben?        T - The Kill
# echo E - The Cage         M - Manhunter        U - Nightmare Tower
# echo F - Demented         N - Maze             V - Valhalla
# echo G - Dogring          O - Mezza
# echo H - Fleshville       P - Mirrored Rooms
# echo.
# choice /C:ABCDEFGHIJKLMNOPQRSTUV /N Please Choose:

# if errorlevel = 22 goto V
# if errorlevel = 21 goto U
# if errorlevel = 20 goto T
# if errorlevel = 19 goto S
# if errorlevel = 18 goto R
# if errorlevel = 17 goto Q
# if errorlevel = 16 goto P
# if errorlevel = 15 goto O
# if errorlevel = 14 goto N
# if errorlevel = 13 goto M
# if errorlevel = 12 goto L
# if errorlevel = 11 goto K
# if errorlevel = 10 goto J
# if errorlevel = 9 goto I
# if errorlevel = 8 goto H
# if errorlevel = 7 goto G
# if errorlevel = 6 goto F
# if errorlevel = 5 goto E
# if errorlevel = 4 goto D
# if errorlevel = 3 goto C
# if errorlevel = 2 goto B
# if errorlevel = 1 goto A

# :A
# cls
# @quake +map ABSTRACT
# goto quit

# :B
# cls
# @quake +map ARENA2
# goto quit

# :C
# cls
# @quake +map ARENAM
# goto quit

# :D
# cls
# @quake +map BATTLE
# goto quit

# :E
# cls
# @quake +map CAGE
# goto quit

# :F
# cls
# @quake +map DEMENTED
# goto quit

# :G
# cls
# @quake +map DOGRING
# goto quit

# :H
# cls
# @quake +map FLESHVIL
# goto quit

# :I
# cls
# @quake +map FLOOD
# goto quit

# :J
# cls
# @quake +map FOUNTAIN
# goto quit

# :K
# cls
# @quake +map GAUNTLET
# goto quit

# :L
# cls
# @quake +map MANDYBEN
# goto quit

# :M
# cls
# @quake +map MANHUNT
# goto quit

# :N
# cls
# @quake +map MAZE
# goto quit

# :O
# cls
# @quake +map MEZZA
# goto quit

# :P
# cls
# @quake +map MIRROR
# goto quit

# :Q
# cls
# @quake +map OFFICE
# goto quit

# :R
# cls
# @quake +map PENTA
# goto quit

# :S
# cls
# @quake +map SPIRAL
# goto quit

# :T
# cls
# @quake +map THEKILL
# goto quit

# :U
# cls
# @quake +map TOWER
# goto quit

# :V
# cls
# @quake +map VALHALLA
# goto quit

# :quit
# exit

# sample bat file 4
# echo off
# cls
# echo.
# echo Press 1 to Host a game
# echo Press 2 to Join a game
# echo Press 3 to Quit
# echo.
# echo Note: To host a game you need port 5000 forwarded
# echo to the host machine.
# echo.
# choice /C:123 /N Please Choose:

# if errorlevel = 3 goto quit
# if errorlevel = 2 goto join
# if errorlevel = 1 goto host

# :host
# cls
# echo.
# serial1 nullmodem port:5000
# cls
# echo.
# echo An null modem connection has been opened on COM 1, port 5000.
# echo.
# echo Other players will need your IP address to join you.
# echo.
# echo Use this IP for internet play:
# type ExtIP.txt
# echo Use this IP for LAN play:
# type ExtIP2.txt
# echo.
# echo Press a key to launch the game. Then choose the following:
# echo In the office, click the gold phone on the table to select MODEM
# echo Ensure Com Port 1 and Direct are selected
# echo Click the Green Arrow to connect
# echo.
# pause
# cd mps\greens
# call greens
# echo.
# echo Thanks for playing.
# echo.
# pause
# exit

# :join
# cls
# echo.
# echo You will need the host's IP address in order to connect to them.
# echo.
# echo When playing within the same network, this will typically start
# echo wityh 192.168.XXX.XXX. If playing over the internet, it will not
# echo start with 192.
# echo.
# askecho /N "set IP=" "+Host's IP Address? " > SetIP.bat
# call setip
# serial1 nullmodem server:%IP% port:5000
# echo.
# echo Press a key to launch the game. Then choose the following:
# echo In the office, click the gold phone on the table to select MODEM
# echo Ensure Com Port 1 and Direct are selected
# echo Click the Green Arrow to connect
# echo.
# pause
# cd mps\greens
# call greens
# echo.
# echo Thanks for playing.
# echo.
# pause
# :later
# exit

# def generate_menus(db_file, id, GameId, path, bat_content):


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
    return json.dumps(result)


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
    if game_id:
        editors = [{'Type': 'IniEditor',
                    'InitActionId': 'GetRunnerConfigActions',
                    'Title': 'Runner',
                    'Description': 'Configures the runner to use with the launcher',
                    'ContentId': shortname}]
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
        return json.dumps({'Type': 'GameDetails', 'Content': {'Details': result}})
    else:
        return None


def get_games_with_images(db_file, image_prefix, filter_str, installed, isLimited, urlencode):
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
    return json.dumps({'Type': 'GameGrid', 'Content': {'Games': result}})


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
                'LaunchOptions':
                {
                    'Exe': options[0],
                    'Options': options[1],
                    'WorkingDir': options[2]
                }
            }
        })


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

    return json.dumps(last_progress_update)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--parsefile', nargs=2, help='Path to the DOSBox configuration file filename and shortname'
    )
    parser.add_argument(
        '--parsejson', help='Configuration shortname, the json is read from stdin'
    )
    parser.add_argument(
        '--updatebats', help='Update bat files')
    parser.add_argument(
        '--parsedir', help='Base directory for DOSBox configuration files')
    parser.add_argument(
        '--conf', nargs='+', help='List of shortnames to reproduce configuration file from database')
    parser.add_argument(
        '--confjson', nargs='+', help='List of shortnames to reproduce configuration file from database'
    )
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
        '--getgameswithimages', nargs='+', help='Get games with images')
    parser.add_argument(
        '--getgamedata', nargs=2, help='Get game data')
    parser.add_argument(
        '--addsteamclientid', nargs=2, help='Add steam client id to game')
    parser.add_argument(
        '--clearsteamclientid', nargs=1, help='Clear steam client id to game'
    )
    parser.add_argument(
        '--findallgamezips', help='Find all game zips'
    )
    parser.add_argument(
        '--getzip', help='Get zip file for shortname'
    )
    parser.add_argument(
        '--launchoptions', nargs=3, help='Launch options'
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

    args = parser.parse_args()
    database.create_tables(args.dbfile)
    if args.parsefile:
        parse_file(args.parsefile[0], args.forkname,
                   args.version, args.platform, args.parsefile[1], args.dbfile)
    if args.parsejson:
        config_data = read_json_from_stdin()
        parse_json_store_in_database(
            args.parsejson, args.forkname, args.version, args.platform, config_data, args.dbfile)
    if args.updatebats:
        batfiles = read_json_from_stdin()
        update_bat_files(args.dbfile, args.updatebats, batfiles)
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
    if args.conf:
        get_config(
            args.conf, args.forkname, args.version, args.platform, args.dbfile)
    if args.confjson:
        print(get_config_json(
            args.confjson, args.forkname, args.version, args.platform, args.dbfile))
    if args.parsemetadata:
        parse_metadata_file(args.parsemetadata, args.dbfile)
    if args.fixshortnames:
        fix_shortnames(args.dbfile)
    if args.findimages:
        find_and_store_images(args.dbfile, args.findimages)
    if args.getgameswithimages:
        filter = ""
        urlencode = False
        if (args.urlencode):
            urlencode = True
        if (len(args.getgameswithimages) > 1):
            filter = args.getgameswithimages[1]
            installed = args.getgameswithimages[2]
            isLimited = args.getgameswithimages[3]
        print(get_games_with_images(args.dbfile,
              args.getgameswithimages[0], filter, installed, isLimited, urlencode))
    if args.getgamedata:
        urlencode = False
        if (args.urlencode):
            urlencode = True
        print(get_game_data(args.dbfile,
              args.getgamedata[0], args.getgamedata[1], urlencode))
    if args.addsteamclientid:
        add_steam_client_id(
            args.addsteamclientid[0], args.addsteamclientid[1], args.dbfile)
    if args.clearsteamclientid:
        clear_steam_client_id(args.clearsteamclientid[0], args.dbfile)
        print(json.dumps({'success': True}))
    if args.findallgamezips:
        find_all_game_zips(args.dbfile, args.findallgamezips)
    if args.getzip:
        urlencode = False
        if (args.urlencode):
            urlencode = True
        print(get_zip_for_shortname(args.getzip, args.dbfile), urlencode)
    if args.launchoptions:
        print(get_lauch_options(args.launchoptions, args.dbfile))
    if args.fixautoexec:
        fix_auto_exec(args.dbfile)
    if args.fixwinautoexec:
        fix_win_auto_exec(args.dbfile)
    if args.extractbatfiles:
        find_all_bat_files(
            args.dbfile, args.extractbatfiles[0], args.extractbatfiles[1])
    if args.patchbatfiles:
        patch_bat_files(args.dbfile)
    if args.writebatfiles:
        write_bat_files(args.dbfile, args.writebatfiles)
    if args.getjsonbats:
        print(get_json_bat_files(args.dbfile, args.getjsonbats))
    if args.getprogress:
        print(get_last_progress_update(args.getprogress))
    if not any(vars(args).values()):
        parser.print_help()


if __name__ == '__main__':
    main()
