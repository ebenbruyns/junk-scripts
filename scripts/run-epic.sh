#!/bin/bash
PLATFORM=Epic
source "${HOME}/bin/settings.sh"

export STEAM_COMPAT_DATA_PATH="${HOME}/.compat/${1}"
mkdir -p $STEAM_COMPAT_DATA_PATH
echo $STEAM_COMPAT_DATA_PATH
export STEAM_COMPAT_CLIENT_INSTALL_PATH=$($EPICCONF --get-working-dir "${1}")
echo $STEAM_COMPAT_CLIENT_INSTALL_PATH

$LEGENDARY launch $1 --no-wine --wrapper "${WRAPPER}" 2>&1 | tee "${HOME}/${1}.log"
