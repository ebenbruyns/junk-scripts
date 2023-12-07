#!/bin/bash
PLATFORM=Epic
# this does not get executed in the context of the plugin so we need to be aware that 
# plugin variables are not available
source "${HOME}/homebrew/data/Junk-Store/scripts/settings.sh"
ARGS=$($EPICCONF --get-args "${1}")
echo $ARGS
export ARGS
