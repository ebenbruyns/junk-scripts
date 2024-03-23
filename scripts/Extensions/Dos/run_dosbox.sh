#!/bin/bash
PLATFORM=Dos
export DECKY_PLUGIN_RUNTIME_DIR="${HOME}/homebrew/data/Junk-Store"
export DECKY_PLUGIN_DIR="${HOME}/homebrew/plugins/Junk-Store"
export DECKY_PLUGIN_LOG_DIR="${HOME}/homebrew/logs/Junk-Store"
source "${DECKY_PLUGIN_RUNTIME_DIR}/scripts/Extensions/Dos/settings.sh"

echo "dbfile: ${DBFILE}"
SETTINGS=$($DOSCONF --get-env-settings $1 --dbfile $DBFILE --platform dos --fork "" --version "" --dbfile $DBFILE)
echo "${SETTINGS}"
eval "${SETTINGS}"

case $DOS_FORKNAME in
    staging)
        echo "staging"
        sleep 10
        DOSBOX="/bin/flatpak run io.github.dosbox-staging"
        ;;
    dosbox)
        echo "dosbox"
        sleep 10
        DOSBOX="/bin/flatpak run com.dosbox.DOSBox"
        ;;
    dosboxx)

        echo "dosboxx"
        sleep 10
        DOSBOX="/bin/flatpak run com.dosbox_x.DOSBox-X"
        ;;
esac
echo "DOSBOX: ${DOSBOX} $@" 
run_dosbox $@

#run other exe

# dosbox -noautoexec -c "mount c ." -c "c:\DOOM\SETUP.EXE" -c "exit" 