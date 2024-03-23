#!/bin/bash

# Register actions with the junk-store.sh script
# ACTIONS+=()

# Register Epic as a platform with the junk-store.sh script
PLATFORMS+=("Windows")


# only source the settings if the platform is Epic - this is to conflicts with other plugins
if [[ "${PLATFORM}" == "Windows" ]]; then
    source "${DECKY_PLUGIN_RUNTIME_DIR}/scripts/${Extensions}/Windows/settings.sh"
fi


function Windows_init(){
    if [[ ! -f "${DECKY_PLUGIN_RUNTIME_DIR}/${DBNAME}" ]]; then
        cp "${DECKY_PLUGIN_RUNTIME_DIR}/dbs/${DBNAME}" "${DECKY_PLUGIN_RUNTIME_DIR}/${DBNAME}"
    fi
}


function get_env_settings(){
   
    SETTINGS=$($DOSCONF --get-env-settings $1 --dbfile $DBFILE --platform dos --forkname "" --version "")
    #echo "${SETTINGS}"
    eval "${SETTINGS}"
}

function Windows_getgames(){
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
            TEMP=$($DOSCONF --getgameswithimages "${IMAGE_PATH}" "${FILTER}" "${INSTALLED}" "${LIMIT}" "${NEEDSLOGIN}" --dbfile $DBFILE --urlencode)
            ;;
           
        *)
            TEMP=$($DOSCONF --getgameswithimages "${IMAGE_PATH}" "${FILTER}" "${INSTALLED}" "${LIMIT}" "${NEEDSLOGIN}" --dbfile $DBFILE)
            ;;
    esac
   
    echo $TEMP
}
function Windows_saveconfig(){
    get_env_settings "${1}"
   
    if [[ -z "${DOS_FORKNAME}" ]]; then
        FORKNAME="staging"
    else
        FORKNAME=$DOS_FORKNAME       
    fi
    input=$(cat)
    echo $input > /tmp/input.json
    TEMP=$(echo $input | $DOSCONF --parsejson "${1}" --platform linux --forkname $FORKNAME --version "" --dbfile $DBFILE)
    
    echo $TEMP
}
function Windows_getconfig(){
     get_env_settings  "${1}"
    #echo "forkname: ${DOS_FORKNAME}"
    if [[ -z "${DOS_FORKNAME}" ]]; then
        FORKNAME="staging"
    else
        FORKNAME=$DOS_FORKNAME       
    fi
    TEMP=$($DOSCONF --confjson "${1}" --platform linux --forkname $FORKNAME --version ""  --dbfile $DBFILE)
    echo $TEMP
}


function Windows_saveplatformconfig(){
    TEMP=$(cat | $DOSCONF --parsejson "${1}" --dbfile $DBFILE --platform dos --forkname "" --version "" --dbfile $DBFILE)
    echo $TEMP
}
function Windows_getplatformconfig(){
    TEMP=$($DOSCONF --confjson "${1}" --platform dos --forkname "" --version "" --dbfile $DBFILE)
    echo $TEMP
}

function Windows_cancelinstall(){
    PID=$(cat "${DECKY_PLUGIN_LOG_DIR}/${1}.pid")
    
    kill -9 $PID
            
          
    
    rm "${DECKY_PLUGIN_LOG_DIR}/${1}.pid"
    echo "{\"Type\": \"Success\", \"Content\": {\"Message\": \"${1} installation cancelled\"}}"
}

function Windows_download(){
     PROGRESS_LOG="${DECKY_PLUGIN_LOG_DIR}/${1}.progress"
    # if [[ -s $PROGRESS_LOG ]]; then
    #     exit 0
    # fi
    
   
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
   
     echo "{\"Type\": \"Progress\", \"Content\": {\"Message\": \"Downloading\"}}"

}
function Windows_getlaunchoptions(){
    TEMP=$($DOSCONF --launchoptions "${LAUNCHER}" "${1}" "${INSTALL_DIR}" "" --dbfile $DBFILE)
    echo $TEMP
    
}

function Windows_install(){
     PROGRESS_LOG="${DECKY_PLUGIN_LOG_DIR}/${1}.progress"
    rm $PROGRESS_LOG &>> "${DECKY_PLUGIN_LOG_DIR}/${1}.log"
    REUSLT=$($DOSCONF --addsteamclientid "${1}" "${2}" --dbfile $DBFILE)
    
    ZIPFILE=$($DOSCONF --getzip "${1}" --dbfile $DBFILE)
    mkdir -p "${INSTALL_DIR}"
    cd "${INSTALL_DIR}"
    case $SOURCE in
        local)
            unzip -o "${ZIP_DIR}/${ZIPFILE}" &>> "${DECKY_PLUGIN_LOG_DIR}/${1}.log"
            ;;
        lan)
            unzip -o "${ZIPFILE}" &>> "${DECKY_PLUGIN_LOG_DIR}/${1}.log"
            rm "${ZIPFILE}" &>> "${DECKY_PLUGIN_LOG_DIR}/${1}.log"
            ;;
        archive)
            unzip -o "${ZIPFILE}" &>> "${DECKY_PLUGIN_LOG_DIR}/${1}.log"
            rm "${ZIPFILE}" &>> "${DECKY_PLUGIN_LOG_DIR}/${1}.log"
            
            ;;
        *)  echo "Unknown source: $SOURCE"
            exit 1
            ;;
    esac
    find "${INSTALL_DIR}" -name CHOICE.EXE -type f -delete 
    TEMP=$($DOSCONF --launchoptions "${LAUNCHER}" "${1}" "${INSTALL_DIR}" "" --dbfile $DBFILE)
    echo $TEMP
            
}

function Windows_uninstall(){
   
    #rm -rf "${INSTALL_DIR}${1}"
           
    TEMP=$($DOSCONF --clearsteamclientid "${1}" --dbfile $DBFILE)
    echo $TEMP
    
    
}
function Windows_getgamedetails(){
    get_env_settings "${1}"
    if [[ -z "${DOS_FORKNAME}" ]]; then
        FORKNAME="staging"
    else
        FORKNAME=$DOS_FORKNAME       
    fi
    IMAGE_PATH="${IMAGE_PATH}"
    case $SOURCE in
        archive)
            TEMP=$($DOSCONF --getgamedata "${1}" "${IMAGE_PATH}" --dbfile $DBFILE --urlencode --forkname $FORKNAME --version "" --platform linux)
            ;;
        *)
            TEMP=$($DOSCONF --getgamedata "${1}" "${IMAGE_PATH}" --dbfile $DBFILE --forkname $FORKNAME --version "" --platform linux)
            ;;
    esac
    
    echo $TEMP
    exit 0
}
function Windows_getbats(){
    TEMP=$($DOSCONF --getjsonbats "${1}" --dbfile $DBFILE)
    echo $TEMP
}
function Windows_savebats(){
    cat | $DOSCONF --updatebats "${1}" --dbfile $DBFILE
}
function Windows_getprogress()
{
    TEMP=$($DOSCONF --getprogress "${DECKY_PLUGIN_LOG_DIR}/${1}.progress" --dbfile $DBFILE)
    echo $TEMP
           
}
function Windows_loginstatus(){
    TEMP=$($EPICCONF --getloginstatus --dbfile $DBFILE)
    echo $TEMP

}
function Windows_getsetting(){
    TEMP=$($DOSCONF --getsetting $1 --dbfile $DBFILE)
    echo $TEMP
}
function Windows_savesetting(){
    $DOSCONF --savesetting $1 $2 --dbfile $DBFILE
}   

function Windows_run-exe(){
    get_steam_env  
    SETTINGS=$($EPICCONF --get-env-settings $ID --dbfile $DBFILE)
    echo "${SETTINGS}"
    eval "${SETTINGS}"
    STEAM_ID="${1}"
    GAME_SHORTNAME="${2}"
    GAME_EXE=$(echo "${3}" | sed 's/\\/\\\\/g' )
    ARGS="${4}"
    if [[ $4 == true ]]; then
        ARGS="some value"
    else
        ARGS=""
    fi
    COMPAT_TOOL="${5}"
    GAME_PATH=$($EPICCONF --get-game-dir $GAME_SHORTNAME --dbfile $DBFILE --offline)
    launchoptions "${LAUNCHER}"  "${GAME_SHORTNAME} ${GAME_EXE}  &> ${DECKY_PLUGIN_LOG_DIR}/${2}run-exe.log" "${INSTALL_DIR}" "RunExe" true "${COMPAT_TOOL}"
}

function Windows_get-exe-list(){
    get_steam_env
    STEAM_ID="${1}"
    GAME_SHORTNAME="${2}"
    cd $INSTALL_DIR
    cd $2
    
    LIST=$(find . \( -iname "*.exe" -o -iname "*.bat" -o -iname "*.com" \) -not \( -ipath "./windows/*" \) -not -ipath "./apps/*" -not -ipath "./sb16/*" )
    JSON="{\"Type\": \"FileContent\", \"Content\": {\"Files\": ["
    for FILE in $LIST; do
        
        JSON="${JSON}{\"Path\": \"${FILE}\"},"
    done
    JSON=$(echo "$JSON" | sed 's/,$//' | sed 's/\.\///g' | sed 's/\//\\\\/g' ) 
    JSON="${JSON}]}}"
    echo $JSON
}



function Windows_getjsonimages(){
    TEMP=$($DOSCONF --get-base64-images "${1}" "${IMAGE_PATH}" --dbfile $DBFILE --urlencode)
    echo $TEMP
}
function Windows_gettabconfig(){
# Check if conf_schemas directory exists, create it if not
    if [[ ! -d "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas" ]]; then
        mkdir -p "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas"
    fi
    if [[ -f "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas/windowstabconfig.json" ]]; then
        TEMP=$(cat "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas/windowstabconfig.json")
    else
        TEMP=$(cat "${DECKY_PLUGIN_DIR}/conf_schemas/windowstabconfig.json")
    fi
    echo "{\"Type\":\"IniContent\", \"Content\": ${TEMP}}"
}
function Windows_savetabconfig(){
    
    cat > "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas/windowstabconfig.json"
    echo "{\"Type\": \"Success\", \"Content\": {\"Message\": \"Windows tab config saved\"}}"
    
}
