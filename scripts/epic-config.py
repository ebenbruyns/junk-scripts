#!/usr/bin/env python
import re
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
import time
import database

cols = database.cols


def execute_shell(cmd):
    # print(f"Executing {cmd}")

    result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                              shell=True, env=os.environ).communicate()[0].decode()
    # print(f"Result: {result}")
    return json.loads(result)

# sample json for game returned from legendary list --json


def get_list(db_file):
    games_list = execute_shell(os.path.expanduser(
        "~/miniconda3/bin/legendary list --json"))
    insert_data(db_file, games_list)


def get_working_dir(game_id):
    result = execute_shell(os.path.expanduser(
        f"~/miniconda3/bin/legendary launch {game_id} --json"))
    print(result['working_directory'])


def insert_data(db_file, games_list):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    for game in games_list:

        try:
            title = game['app_title']
            notes = game['metadata']['description']
            application_path = ""
            manual_path = ""
            publisher = game['metadata']['developer']
            root_folder = ""
            source = "Epic"
            database_id = game['app_name']
            genre = ""
            configuration_path = ""
            developer = game['metadata']['developer']
            release_date = game['metadata']['creationDate']
            shortname = game['asset_infos']['Windows']['asset_id']

            c.execute("SELECT * FROM Game WHERE ShortName=?", (shortname,))
            result = c.fetchone()
            if result is None:
                vals = []

                vals.append(title.replace("'", "''"))
                vals.append(notes.replace("'", "''"))
                vals.append(application_path)
                vals.append(manual_path)
                vals.append(publisher.replace("'", "''"))
                vals.append(root_folder)
                vals.append(source)
                vals.append(database_id)
                vals.append(genre)
                vals.append(configuration_path)
                vals.append(developer.replace("'", "''"))
                vals.append(release_date)

                vals.append("")
                vals.append(shortname)
                # print(f"Inserting game {title} into database: {vals}")

                placeholders = ', '.join(['?' for _ in range(len(cols))])
                cols_with_pk = cols + ["SteamClientID", "ShortName"]
                placeholders = ', '.join(
                    ['?' for _ in range(len(cols_with_pk))])
                tmp = f"INSERT INTO Game ({', '.join(cols_with_pk)}) VALUES ({placeholders})"
                # print(tmp)
                c.execute(tmp, vals)

                game_id = c.lastrowid
                # Insert images into the Images table
                for image in game['metadata']['keyImages']:
                    c.execute(
                        "INSERT INTO Images (GameID, ImagePath, FileName, SortOrder) VALUES (?, ?, ?, ?)", (game_id, image['url'], '', image['width']))

        except Exception as e:
            print(f"Error parsing metadata for game: {title} {e}")

    conn.commit()
    conn.close()


def insert_game(db_file, game):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

# [DLManager] INFO: = Progress: 0.51% (368/72002), Running for 00:01:58, ETA: 06:23:02
# [DLManager] INFO:  - Downloaded: 316.12 MiB, Written: 361.03 MiB
# [DLManager] INFO:  - Cache usage: 35.00 MiB, active tasks: 32
# [DLManager] INFO:  + Download	- 4.00 MiB/s (raw) / 4.00 MiB/s (decompressed)
# [DLManager] INFO:  + Disk	- 2.00 MiB/s (write) / 0.00 MiB/s (read)


def calculate_total_size(progress_percentage, written_size):
    return round(written_size * (progress_percentage / 100), 2)


def get_last_progress_update(file_path):
    progress_re = re.compile(
        r"\[DLManager\] INFO: = Progress: (\d+\.\d+)% \((\d+)/(\d+)\), Running for (\d+:\d+:\d+), ETA: (\d+:\d+:\d+)\n\[DLManager\] INFO:  - Downloaded: (\d+\.\d+) MiB, Written: (\d+\.\d+) MiB\n\[DLManager\] INFO:  - Cache usage: (\d+\.\d+) MiB, active tasks: (\d+)\n\[DLManager\] INFO:  \+ Download\t- (\d+\.\d+) MiB/s \(raw\) / (\d+\.\d+) MiB/s \(decompressed\)\n\[DLManager\] INFO:  \+ Disk\t- (\d+\.\d+) MiB/s \(write\) / (\d+\.\d+) MiB/s \(read\)")
    last_progress_update = None

    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
            for i in range(len(lines) - 5):
                match = progress_re.search(''.join(lines[i:i+6]))
                if match:
                    last_progress_update = {
                        "Percentage": float(match.group(1)),
                        "Description": f"Downloaded {match.group(2)} MB of {match.group(3)} MB ({match.group(1)}%)\nSpeed: {match.group(11)} MB/s"
                    }

    except Exception as e:
        print("Waiting for progress update", e, file=sys.stderr)
        time.sleep(1)

    return json.dumps({'Type': 'ProgressUpdate', 'Content': last_progress_update})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--list', help='Get list of epic games', action='store_true')
    parser.add_argument(
        '--dbfile', help='Path to the SQLite database file', default='configs.db')
    parser.add_argument(
        '--get-working-dir', help='Get working directory for game')
    parser.add_argument(
        '--getprogress', help='Get installtion progress for game')

    database.create_tables(parser.parse_args().dbfile)
    args = parser.parse_args()
    if args.list:
        print(get_list(args.dbfile))
    if args.get_working_dir:
        get_working_dir(args.get_working_dir)
    if args.getprogress:
        print(get_last_progress_update(args.getprogress))
    if not any(vars(args).values()):
        parser.print_help()


if __name__ == '__main__':
    main()
