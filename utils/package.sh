#!/bin/bash
set -x
mkdir -p junk-store-decky/bin
mkdir -p junk-store-decky/data
mkdir -p junk-store-decky/db

cp install.sh junk-store-decky/
cp settings.sh junk-store-decky/bin
cp junk-store.sh junk-store-decky/bin
cp dosbox-conf.py junk-store-decky/bin
cp epic-config.py junk-store-decky/bin
cp run-epic.sh junk-store-decky/bin
cp run_dosbox.sh junk-store-decky/bin
cp settings.sh junk-store-decky/bin
cp serve_exodos.sh junk-store-decky/bin
cp run_win_dosbox.sh junk-store-decky/bin
cp ~/junk-store-decky/winconfigs.db junk-store-decky/db
cp ~/junk-store-decky/configs.db junk-store-decky/db
cp -rf ~/homebrew/data/junk-store/* junk-store-decky/data
cp ~/homebrew/plugins/junk-store/out/Junk\ Store.zip junk-store-decky/junk-store.zip

zip -r junk-store-decky.zip junk-store-decky

