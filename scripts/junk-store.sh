#!/bin/bash
source "${DECKY_PLUGIN_RUNTIME_DIR}/scripts/settings.sh"


function init() {
    $EPICCONF --list --dbfile $EPICDB > /dev/null
}
function getgames(){
    if [ -z "${1}" ]; then
        FILTER=""
    else
        FILTER="${1}"
    fi
   
    if [ -z "${2}" ]; then
        INSTALLED="false"
    else
        INSTALLED="${2}"
    fi
     if [ -z "${3}" ]; then
        LIMIT="true"
    else
        LIMIT="${3}"
    fi
    case $PLATFORM in
        Epic)
            IMAGE_PATH=""
            ;;
        *)
            IMAGE_PATH="${IMAGE_PATH}"
            ;;
    esac
     case $SOURCE in
        archive)
            case $PLATFORM in
                Epic)
                    TEMP=$($DOSCONF --getgameswithimages "${IMAGE_PATH}" "${FILTER}" "${INSTALLED}" "${LIMIT}" "${NEEDSLOGIN}" --dbfile $DBFILE)
                    ;;
                *)
                TEMP=$($DOSCONF --getgameswithimages "${IMAGE_PATH}" "${FILTER}" "${INSTALLED}" "${LIMIT}" "${NEEDSLOGIN}" --dbfile $DBFILE --urlencode)
                ;;
            esac
            ;;
        *)
             TEMP=$($DOSCONF --getgameswithimages "${IMAGE_PATH}" "${FILTER}" "${INSTALLED}" "${LIMIT}" "${NEEDSLOGIN}" --dbfile $DBFILE)
            ;;
    esac
   
    echo $TEMP
}
function saveconfig(){
    cat | $DOSCONF --parsejson "${1}" --dbfile $DBFILE 
}
function getconfig(){
    TEMP=$($DOSCONF --confjson "${1}"  --dbfile $DBFILE)
    echo $TEMP
}




function cancelinstall(){
    PID=$(cat "${DECKY_PLUGIN_LOG_DIR}/${1}.pid")
    case $PLATFORM in
        Epic)
            killall -w legendary
            rm "${DECKY_PLUGIN_LOG_DIR}/tmp.pid"
            ;;
            
        *)
            kill -9 $PID
            
            ;;
    esac
    
    rm "${DECKY_PLUGIN_LOG_DIR}/${1}.pid"
    echo "{\"Type\": \"Success\", \"Content\": {\"Message\": \"Cancelled\"}}"
}

function download(){
    PROGRESS_LOG="${DECKY_PLUGIN_LOG_DIR}/${1}.progress"
    # if [[ -s $PROGRESS_LOG ]]; then
    #     exit 0
    # fi
    
    case $PLATFORM in
        Epic)
            ${LEGENDARY} install ${1} --force --with-dlcs -y --platform Windows >> "${DECKY_PLUGIN_LOG_DIR}/${1}.log" 2>> $PROGRESS_LOG &
            echo $! > "${DECKY_PLUGIN_LOG_DIR}/${1}.pid"
            ;;
        *)
            case $SOURCE in
                archive)
                    ZIPFILE=$($DOSCONF --getzip "${1}" --dbfile $DBFILE --urlencode)
                    ;;
                *)
                    ZIPFILE=$($DOSCONF --getzip "${1}" --dbfile $DBFILE)
                    ;;
            esac
            mkdir -p "${INSTALL_DIR}"
            cd "${INSTALL_DIR}"
            case $SOURCE in
                local)
                    unzip -o "${ZIP_DIR}/${ZIPFILE}" > /dev/null
                    ;;
                lan)
                    URL="${ZIP_DIR}/${ZIPFILE}"
                    PID=$(wget -b -c "${URL}" -o "${PROGRESS_LOG}" >> "${PROGRESS_LOG}")
                    PID=$(echo $PID | cut -d' ' -f 5 | cut -d'.' -f 1)
                    echo $PID > "${DECKY_PLUGIN_LOG_DIR}/${1}.pid"
                    ;;
                archive)
                    URL="${ZIP_DIR}/${ZIPFILE}"
                    PID=$(wget -b -c "${URL}" -o "${PROGRESS_LOG}")
                    PID=$(echo $PID | cut -d' ' -f 5 | cut -d'.' -f 1)
                    echo $PID > "${DECKY_PLUGIN_LOG_DIR}/${1}.pid"
                    ;;
                *)  echo "Unknown source: $SOURCE"
                    exit 1
                    ;;
            esac
            ;;
    esac
    echo "{\"Type\": \"Success\", \"Content\": {\"Message\": \"Downloading\"}}"

}
function getlaunchoptions(){
    case $PLATFORM in
        Epic)
            ARGS=$($ARGS_SCRIPT "${1}")
            TEMP=$($EPICCONF --launchoptions "${1}" "${ARGS}" "" --dbfile $DBFILE)
            echo $TEMP
            exit 0
            ;;
        *)
            TEMP=$($DOSCONF --launchoptions "${LAUNCHER}" "${1}" "${INSTALL_DIR}" "" --dbfile $DBFILE)
            echo $TEMP
            exit 0
            ;;
    esac
    
}

function install(){
    PROGRESS_LOG="${DECKY_PLUGIN_LOG_DIR}/${1}.progress"
    rm $PROGRESS_LOG
    case $PLATFORM in
        Epic)
            PROGRESS_LOG="${DECKY_PLUGIN_LOG_DIR}/${1}.progress"
            rm $PROGRESS_LOG

            RESULT=$($DOSCONF --addsteamclientid "${1}" "${2}" --dbfile $DBFILE)
            #WORKING_DIR=$($EPICCONF --get-working-dir "${1}")
            #mkdir -p "${HOME}/.compat/${1}"
            ARGS=$($ARGS_SCRIPT "${1}")
            TEMP=$($EPICCONF --launchoptions "${1}" "${ARGS}" "" --dbfile $DBFILE)
            echo $TEMP
            exit 0
            ;;
        *)
            REUSLT=$($DOSCONF --addsteamclientid "${1}" "${2}" "" --dbfile $DBFILE)
            ZIPFILE=$($DOSCONF --getzip "${1}" --dbfile $DBFILE)
            mkdir -p "${INSTALL_DIR}"
            cd "${INSTALL_DIR}"
            case $SOURCE in
                local)
                    unzip -o "${ZIP_DIR}/${ZIPFILE}" > /dev/null
                    ;;
                lan)
                    unzip -o "${ZIPFILE}" > /dev/null
                    rm "${ZIPFILE}" 
                    ;;
                archive)
                    unzip -o "${ZIPFILE}" > /dev/null
                    rm "${ZIPFILE}" 
                    
                    ;;
                *)  echo "Unknown source: $SOURCE"
                    exit 1
                    ;;
            esac
            find "${INSTALL_DIR}" -name CHOICE.EXE -type f -delete 
            TEMP=$($DOSCONF --launchoptions "${LAUNCHER}" "${1}" "${INSTALL_DIR}" "" --dbfile $DBFILE)
            echo $TEMP
            exit 0
     ;;
    esac
}

function uninstall(){
    case $PLATFORM in
        Epic)
            WORKING_DIR=$($EPICCONF --get-working-dir "${1}")
            rm -rf "${WORKING_DIR}"
            ;;
        Dos)
            rm -rf "${INSTALL_DIR}${1}"
            ;;
        Windows)
            rm -rf "${INSTALL_DIR}${1}"
            ;;
    esac
    TEMP=$($DOSCONF --clearsteamclientid "${1}" --dbfile $DBFILE)
    echo $TEMP
    
}
function getgamedetails(){
    case $PLATFORM in
        Epic)
            IMAGE_PATH=""
            ;;
        *)
            IMAGE_PATH="${IMAGE_PATH}"
            ;;
    esac
    case $SOURCE in
        archive)
            case $PLATFORM in 
                Epic)
                    TEMP=$($DOSCONF --getgamedata "${1}" "${IMAGE_PATH}" --dbfile $DBFILE)
                    ;;
                *)
                TEMP=$($DOSCONF --getgamedata "${1}" "${IMAGE_PATH}" --dbfile $DBFILE --urlencode)
                    ;;
            esac
            ;;
        *)
            TEMP=$($DOSCONF --getgamedata "${1}" "${IMAGE_PATH}" --dbfile $DBFILE)
            ;;
    esac
    
    echo $TEMP
    exit 0
}
function getbats(){
    TEMP=$($DOSCONF --getjsonbats "${1}" --dbfile $DBFILE)
    echo $TEMP
}
function savebats(){
    cat | $DOSCONF --updatebats "${1}" --dbfile $DBFILE
}
function getprogress()
{
    case $PLATFORM in
        Epic)
            TEMP=$($EPICCONF --getprogress "${DECKY_PLUGIN_LOG_DIR}/${1}.progress"  --dbfile $DBFILE)
            echo $TEMP
            ;;
        *)
            TEMP=$($DOSCONF --getprogress "${DECKY_PLUGIN_LOG_DIR}/${1}.progress" --dbfile $DBFILE)
            echo $TEMP
            ;;
    esac
}
function loginstatus(){
    TEMP=$($EPICCONF --getloginstatus --dbfile $DBFILE)
    echo $TEMP

}
function login(){
    #TEMP=$($LEGENDARY auth)
    TEMP=$($DOSCONF --launchoptions "/bin/flatpak" "run com.github.derrod.legendary auth" "" "Epic Games Login" --dbfile $DBFILE)
    echo $TEMP
}

function logout(){
    TEMP=$($LEGENDARY auth --delete)
    loginstatus
}

function getsetting(){
    TEMP=$($DOSCONF --getsetting $1 --dbfile $DBFILE)
    echo $TEMP
}
function savesetting(){
    $DOSCONF --savesetting $1 $2 --dbfile $DBFILE
}   

ACTION=$1
shift


case $ACTION in
    init)
        init "${@}"
        ;;
    getgames)
        getgames "${@}"
        ;;
    getactions)
        getactions "${@}"
        ;;
    saveconfig)
        saveconfig "${@}"
        ;;
    getconfig)
        getconfig "${@}"
        ;;
    download)
        download "${@}"
        ;;
    install)
        install "${@}"
        ;;
    cancelinstall)
        cancelinstall "${@}"
        ;;
    uninstall)
        uninstall "${@}"
        ;;
    getgamedetails)
        getgamedetails "${@}"
        ;;
    getbats)
        getbats "${@}"
        ;;
    savebats)
        savebats "${@}"
        ;;
    getprogress)
        getprogress "${@}"
        ;;
    login)
        login "${@}"
        ;;
    logout)
        logout "${@}"
        ;;
    loginstatus)
        loginstatus "${@}"
        ;;
    getsetting)
        getsetting "${@}"
        ;;
    savesetting)
        savesetting "${@}"
        ;; 
    *)
        echo "Unknown command: ${ACTION}"
        exit 1
        ;;
esac
