#!/bin/bash

# Register actions with the junk-store.sh script
# ACTIONS+=()

# Register Epic as a platform with the junk-store.sh script
PLATFORMS+=("Dos")


# only source the settings if the platform is Dos - this is to avoid conflicts with other plugins
if [[ "${PLATFORM}" == "Dos" ]]; then
    source "${DECKY_PLUGIN_RUNTIME_DIR}/scripts/${Extensions}/Dos/settings.sh"
fi

function Dos_init(){
    if [[ ! -f "${DECKY_PLUGIN_RUNTIME_DIR}/${DBNAME}" ]]; then
        cp "${DECKY_PLUGIN_RUNTIME_DIR}/dbs/${DBNAME}" "${DECKY_PLUGIN_RUNTIME_DIR}/${DBNAME}"
    fi
}

function get_env_settings(){
   
    SETTINGS=$($DOSCONF --get-env-settings $1 --dbfile $DBFILE --platform dos --forkname "" --version "")
    #echo "${SETTINGS}"
    eval "${SETTINGS}"
}

function Dos_getgames(){
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
   
    IMAGE_PATH="${IMAGE_PATH}"
         
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
function Dos_saveconfig(){
    
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
function Dos_getconfig(){
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

function Dos_saveplatformconfig(){
    TEMP=$(cat | $DOSCONF --parsejson "${1}" --dbfile $DBFILE --platform dos --forkname "" --version "" --dbfile $DBFILE)
    echo $TEMP
}
function Dos_getplatformconfig(){
    TEMP=$($DOSCONF --confjson "${1}" --platform dos --forkname "" --version "" --dbfile $DBFILE)
    echo $TEMP
}



function Dos_cancelinstall(){
    PID=$(cat "${DECKY_PLUGIN_LOG_DIR}/${1}.pid")
    
    kill -9 $PID
            
          
    
    rm "${DECKY_PLUGIN_LOG_DIR}/${1}.pid"
    echo "{\"Type\": \"Success\", \"Content\": {\"Message\": \"${1} installaion cancelled\"}}"
}

function Dos_download(){
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
function Dos_getlaunchoptions(){
    TEMP=$($DOSCONF --launchoptions "${LAUNCHER}" "${1}" "${INSTALL_DIR}" "" --dbfile $DBFILE)
    echo $TEMP
}

#function Dos_move(){
  
#}


function Dos_install(){
    PROGRESS_LOG="${DECKY_PLUGIN_LOG_DIR}/${1}.progress"
    rm $PROGRESS_LOG &>> "${DECKY_PLUGIN_LOG_DIR}/${1}.log"
    REUSLT=$($DOSCONF --addsteamclientid "${1}" "${2}" --dbfile $DBFILE)
    
    ZIPFILE=$($DOSCONF --getzip "${1}" --dbfile $DBFILE)
    mkdir -p "${INSTALL_DIR}"
    cd "${INSTALL_DIR}"
    echo "unzipping ${ZIPFILE}" &>> "${DECKY_PLUGIN_LOG_DIR}/${1}.log"
    echo "unzipping to ${INSTALL_DIR}" &>> "${DECKY_PLUGIN_LOG_DIR}/${1}.log"
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

function Dos_uninstall(){
  
    #rm -rf "${INSTALL_DIR}${1}"
           
    TEMP=$($DOSCONF --clearsteamclientid "${1}" --dbfile $DBFILE)
    echo $TEMP
    
}
function Dos_getgamedetails(){
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
function Dos_getbats(){
    TEMP=$($DOSCONF --getjsonbats "${1}" --dbfile $DBFILE)
    echo $TEMP
}
function Dos_savebats(){
    cat | $DOSCONF --updatebats "${1}" --dbfile $DBFILE
}
function Dos_getprogress()
{
    TEMP=$($DOSCONF --getprogress "${DECKY_PLUGIN_LOG_DIR}/${1}.progress" --dbfile $DBFILE)
    echo $TEMP
}

function Dos_getsetting(){
    TEMP=$($DOSCONF --getsetting $1 --dbfile $DBFILE)
    echo $TEMP
}
function Dos_savesetting(){
    $DOSCONF --savesetting $1 $2 --dbfile $DBFILE
}   

function Dos_run-exe(){
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

function Dos_get-exe-list(){
    get_steam_env
    STEAM_ID="${1}"
    GAME_SHORTNAME="${2}"
    cd $INSTALL_DIR
    cd $2
    LIST=$(find . \( -iname "*.exe" -o -iname "*.bat" -o -iname "*.com" \))
    JSON="{\"Type\": \"FileContent\", \"Content\": {\"Files\": ["
    for FILE in $LIST; do
        
        JSON="${JSON}{\"Path\": \"${FILE}\"},"
    done
    JSON=$(echo "$JSON" | sed 's/,$//' | sed 's/\.\//c:\\\\/g' | sed 's/\//\\\\/g' ) 
    JSON="${JSON}]}}"
    echo $JSON
}


function Dos_getsetting(){
    TEMP=$($DOSCONF --getsetting $1 --dbfile $DBFILE)
    echo $TEMP
}
function Dos_savesetting(){
    $DOSCONF --savesetting $1 $2 --dbfile $DBFILE
}   
function Dos_getjsonimages(){
    
    TEMP=$($DOSCONF --get-base64-images "${1}" "${IMAGE_PATH}" --dbfile $DBFILE --urlencode)
    echo $TEMP
}
function Dos_gettabconfig(){
# Check if conf_schemas directory exists, create it if not
    if [[ ! -d "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas" ]]; then
        mkdir -p "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas"
    fi
    if [[ -f "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas/dostabconfig.json" ]]; then
        TEMP=$(cat "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas/dostabconfig.json")
    else
        TEMP=$(cat "${DECKY_PLUGIN_DIR}/conf_schemas/dostabconfig.json")
    fi
    echo "{\"Type\":\"IniContent\", \"Content\": ${TEMP}}"
}
function Dos_savetabconfig(){
    
    cat > "${DECKY_PLUGIN_RUNTIME_DIR}/conf_schemas/dostabconfig.json"
    echo "{\"Type\": \"Success\", \"Content\": {\"Message\": \"Dos Tab Config Saved\"}}"
    
}
function Dos_getgamesize(){
    case $SOURCE in
        archive)
            ZIPFILE=$($DOSCONF --getzip "${1}" --dbfile $DBFILE --urlencode)
            ;;
        *)
            ZIPFILE=$($DOSCONF --getzip "${1}" --dbfile $DBFILE)
            ;;
    esac
    case $SOURCE in
        local)
            URL="${ZIP_DIR}/${ZIPFILE}"
            ;;
        lan)
            URL="${ZIP_DIR}/${ZIPFILE}"
            ;;           
        archive)
            URL="${ZIP_DIR}/${ZIPFILE}"
            
            ;;
        *)  echo "Unknown source: $SOURCE"
            exit 1
            ;;
    esac
    TEMP=$($DOSCONF --get-game-size "${1}" "${URL}" "${2}" --dbfile $DBFILE)
    echo $TEMP
}