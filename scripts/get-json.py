#!/usr/bin/env python3
import sys
import json


json_fragments = {
    "junk-store-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "JunkStoreActions",
            "Actions": [
                {
                    "Id": "GetEpicActions",
                    "Title": "Get Epic store actions",
                    "Type": "Init",
                    "Command": "~/bin/get-json.py epic-actions"
                },
                {
                    "Id": "GetContent",
                    "Title": "Get content",
                    "Type": "TabPage",
                    "Command": "~/bin/get-json.py junk-store-tabs"
                }
            ]
        }
    },
    "main-menu-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "MainMenu",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Populate Store",
                    "Type": "GetContent",
                    "Command": "~/bin/get-json.py main-menu-content"
                },
                {
                    "Id": "JunkStoreInit",
                    "Title": "Content",
                    "Type": "Init",
                    "Command": "~/bin/get-json.py junk-store-actions"
                }
            ]
        }
    },
    "junk-store-tabs": {
        "Type": "StoreTabs",
        "Content": {
            "Tabs": [
                {"Title": "Epic", "Type": "GameGrid", "ActionId": "GetEpicActions"}
            ]
        }
    },
    "main-menu-content": {
        "Type": "MainMenu",
        "Content": {
            "Panels": [
                {
                    "Title": "Custom Stores",
                    "Type": "Section",
                    "Actions": [
                        {
                            "ActionId": "JunkStoreInit",
                            "Title": "Junk's Store",
                            "Type": "Page"
                        }
                    ]
                }
            ]
        }
    },
    "epic-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "EpicActions",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Get Epic games list",
                    "Type": "GameGrid",
                    "Command": "~/bin/junk-store.sh Epic getgames"
                },
                {
                    "Id": "GetDetails",
                    "Title": "Get game details",
                    "Type": "GameDetails",
                    "Command": "~/bin/junk-store.sh Epic getgamedetails"
                },
                {
                    "Id": "Install",
                    "Title": "Install game",
                    "Type": "Install",
                    "Command": "~/bin/junk-store.sh Epic install"
                },
                {
                    "Id": "Download",
                    "Title": "Download game",
                    "Type": "Download",
                    "Command": "~/bin/junk-store.sh Epic download"
                },
                {
                    "Id": "Uninstall",
                    "Title": "Uninstall game",
                    "Type": "Uninstall",
                    "Command": "~/bin/junk-store.sh Epic uninstall"
                },
                {
                    "Id": "GetProgress",
                    "Title": "Get install progress",
                    "Type": "GetProgress",
                    "Command": "~/bin/junk-store.sh Epic getprogress"
                },
                {
                    "Id": "CancelInstall",
                    "Title": "Cancel install",
                    "Type": "CancelInstall",
                    "Command": "~/bin/junk-store.sh Epic cancelinstall"
                }
            ]
        }
    }
}

# Check if an argument is provided
if len(sys.argv) < 2:
    error = {
        "Type": "Error",
        "Content": {
            "Title": "Error",
            "Message": "Please provide an argument."
        }
    }
    print(json.dumps(error))
    sys.exit(1)

# Get the argument from the command line
argument = sys.argv[1]

# Look up the JSON fragment based on the argument
if argument in json_fragments:
    json_fragment = json_fragments[argument]
    print(json.dumps(json_fragment))
else:
    error = {
        "Type": "Error",
        "Content": {
            "Title": "Error",
            "Message": "Invalid argument."
        }
    }
    print(json.dumps(error))
    sys.exit(1)
