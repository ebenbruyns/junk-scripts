#!/bin/bash
# local, lan
# changes the source of the games [local, lan]
SOURCE=archive
# changes the platform of the games [deck, pc]
HOSTTYPE=deck
# add miniconda to path
PATH=$HOME/miniconda3/bin:$PATH
# the path to the dosbox-conf.py script
DOSCONF="${DECKY_PLUGIN_DIR}/scripts/dosbox-conf.py"
EPICCONF="${DECKY_PLUGIN_DIR}/scripts/epic-config.py"
BASE_PATH="Games/exo"
ASSETS_PATH="assets/exo"
#LEGENDARY="${HOME}/miniconda3/bin/legendary"

    
# the install location of the games
INSTALL_DIR="${HOME}/Games/sdos/"
# the launcher script to use in steam
LAUNCHER="${DECKY_PLUGIN_RUNTIME_DIR}/scripts/${Extensions}/Dos/run_dosbox.sh"
IMAGES="Images/MS-DOS"
ZIPS="eXoDOS/eXo/eXoDOS"
SETNAME="eXoDOS"
DBNAME="dosconfigs.db"
NEEDSLOGIN="false"


case $HOSTTYPE in
    deck)
        DBPATH="${DECKY_PLUGIN_RUNTIME_DIR}"
       
        DOSBOX="/bin/flatpak run io.github.dosbox-staging"
        ;;
    *)
        DBPATH="${DECKY_PLUGIN_RUNTIME_DIR}"
       
        DOSBOX="/usr/bin/dosbox-staging"
        ;;
esac

# database to use for configs and metadata
DBFILE="${DBPATH}/${DBNAME}"




case $SOURCE in
    local)
        #CONTENT_SERVER="http://localhost:1337/plugins"
        # SERVER should be mostly ok unless you run your own server - there might be permissions issues though with decky loader
        # if that's the case you might have to change the permissions of the assets folder
        SERVER="${CONTENT_SERVER}/${DECKY_PLUGIN_NAME}/${ASSETS_PATH}"
        # Change this to the location of your eXoDOS folder
        ZIP_DIR="${HOME}/${BASE_PATH}/${ZIPS}/"
        IMAGE_PATH="${SERVER}/${SETNAME}/${IMAGES}/"
        ;;
    lan)
        # Change this to the location of your server serving up eXoDOS
        SERVER="http://192.168.8.100:9000"
        # Change this to the location of the zipped games on the server
        ZIP_DIR="${SERVER}/${ZIPS}/"
        IMAGE_PATH="${SERVER}/${SETNAME}/${IMAGES}/"
        ;;
    archive)
        SERVER="https://archive.org/download/exov5_2/Content/XODOSMetadata.zip/"
        ZIP_DIR="https://archive.org/download/exov5_2/eXo/eXoDOS/"
       
        IMAGE_PATH="${SERVER}${IMAGES}/"
        ;;
    *)  echo "Unknown source: $SOURCE"
        exit 1
        ;;
esac


# this is used by the runner scripts, keeping is central so changes happen in one place
function run_dosbox(){
    $DOSCONF --conf "${1}" --dbfile $DBFILE
    $DOSCONF --writebatfiles "${1}" --dbfile $DBFILE

    extip=$(curl -sf ident.me || curl -sf tnedi.me)
    echo "$extip" >  "${INSTALL_DIR}/${1}/ExtIP.txt"
    ipaddress=`ip -4 -o addr show up primary scope global | sed -e "s|^.*inet \(.*\)/.*|\1\r|"`
    echo "$ipaddress" >  "${INSTALL_DIR}/${1}/ExtIP2.txt"

    $DOSBOX
}
