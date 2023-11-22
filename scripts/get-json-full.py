
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
                    "Command": "~/bin/get-json.sh epic-actions"
                },
                {
                    "Id": "GetDosActions",
                    "Title": "dos games actions",
                    "Type": "Init",
                    "Command": "~/bin/get-json.sh dos-actions"
                },
                {
                    "Id": "GetWindowsActions",
                    "Title": "Windows games actions",
                    "Type": "Init",
                    "Command": "~/bin/get-json.sh windows-actions"
                },
                {
                    "Id": "GetContent",
                    "Title": "Get content",
                    "Type": "TabPage",
                    "Command": "~/bin/get-json.sh junk-store-tabs"
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
                    "Command": "~/bin/get-json.sh main-menu-content"
                },
                {
                    "Id": "JunkStoreInit",
                    "Title": "Content",
                    "Type": "Init",
                    "Command": "~/bin/get-json.sh junk-store-actions"
                },
                {
                    "Id": "SideBarPageInit",
                    "Title": "SideBar",
                    "Type": "Init",
                    "Command": "~/bin/get-json.sh sidebar-page-actions"
                },
                {
                    "Id": "dos-store",
                    "Title": "DOS Store",
                    "Type": "Store",
                    "Command": "~/bin/get-json.sh dos-store"
                }
            ]
        }
    },
    "junk-store-tabs": {
        "Type": "StoreTabs",
        "Content": {
            "Tabs": [
                {"Title": "Dos", "Type": "GameGrid", "ActionId": "GetDosActions"},
                {
                    "Title": "Windows",
                    "Type": "GameGrid",
                    "ActionId": "GetWindowsActions"
                },
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
                        },
                        {
                            "ActionId": "SideBarPageInit",
                            "Title": "Side bar page",
                            "Type": "Page"
                        }
                    ]
                },
                {
                    "Title": "DOS",
                    "Type": "Section",
                    "Actions": [
                        {"ActionId": "dos-store",
                            "Title": "User's Store", "Type": "Page"}
                    ]
                }
            ]
        }
    },
    "dos-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "DosActions",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Get dos games list",
                    "Type": "GameGrid",
                    "Command": "~/bin/junk-store.sh Dos getgames"
                },
                {
                    "Id": "GetDetails",
                    "Title": "Get game details",
                    "Type": "GameDetails",
                    "Command": "~/bin/junk-store.sh Dos getgamedetails"
                },
                {
                    "Id": "Install",
                    "Title": "Install game",
                    "Type": "Install",
                    "Command": "~/bin/junk-store.sh Dos install"
                },
                {
                    "Id": "Download",
                    "Title": "Download game",
                    "Type": "Download",
                    "Command": "~/bin/junk-store.sh Dos download"
                },
                {
                    "Id": "Uninstall",
                    "Title": "Uninstall game",
                    "Type": "Uninstall",
                    "Command": "~/bin/junk-store.sh Dos uninstall"
                },
                {
                    "Id": "GetProgress",
                    "Title": "Get install progress",
                    "Type": "GetProgress",
                    "Command": "~/bin/junk-store.sh Dos getprogress"
                },
                {
                    "Id": "CancelInstall",
                    "Title": "Cancel install",
                    "Type": "CancelInstall",
                    "Command": "~/bin/junk-store.sh Dos cancelinstall"
                },
                {
                    "Id": "GetDosboxConfigFileActions",
                    "Title": "Get dosbox config file actions",
                    "Type": "Init",
                    "Command": "~/bin/get-json.sh dos-config-actions"
                },
                {
                    "Id": "GetBatFileActions",
                    "Title": "Get dosbox config file actions",
                    "Type": "Init",
                    "Command": "~/bin/get-json.sh dos-bat-actions"
                }
            ]
        }
    },
    "windows-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "WindowsActions",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Get Windows games list",
                    "Type": "GameGrid",
                    "Command": "~/bin/junk-store.sh Windows getgames"
                },
                {
                    "Id": "GetDetails",
                    "Title": "Get game details",
                    "Type": "GameDetails",
                    "Command": "~/bin/junk-store.sh Windows getgamedetails"
                },
                {
                    "Id": "Install",
                    "Title": "Install game",
                    "Type": "Install",
                    "Command": "~/bin/junk-store.sh Windows install"
                },
                {
                    "Id": "Download",
                    "Title": "Download game",
                    "Type": "Download",
                    "Command": "~/bin/junk-store.sh Windows download"
                },
                {
                    "Id": "Uninstall",
                    "Title": "Uninstall game",
                    "Type": "Uninstall",
                    "Command": "~/bin/junk-store.sh Windows uninstall"
                },
                {
                    "Id": "GetProgress",
                    "Title": "Get install progress",
                    "Type": "GetProgress",
                    "Command": "~/bin/junk-store.sh Windows getprogress"
                },
                {
                    "Id": "CancelInstall",
                    "Title": "Cancel install",
                    "Type": "CancelInstall",
                    "Command": "~/bin/junk-store.sh Windows cancelinstall"
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
    },
    "dos-bat-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "DosBatEditor",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Get the bat files as json",
                    "Type": "BatEditor",
                    "Command": "~/bin/junk-store.sh Dos getbats"
                },
                {
                    "Id": "SaveContent",
                    "Title": "Save the bat files as json",
                    "Type": "BatEditor",
                    "Command": "~/bin/junk-store.sh Dos savebats"
                }
            ]
        }
    },
    "windows-bat-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "WindowsBatEditor",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Get the bat files as json",
                    "Type": "BatEditor",
                    "Command": "~/bin/junk-store.sh Windows getbats"
                },
                {
                    "Id": "SaveContent",
                    "Title": "Save the bat files as json",
                    "Type": "BatEditor",
                    "Command": "~/bin/junk-store.sh Windows savebats"
                }
            ]
        }
    },
    "dos-config-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "DosConfigEditor",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Get the bat files as json",
                    "Type": "BatEditor",
                    "Command": "~/bin/junk-store.sh Dos getconfig"
                },
                {
                    "Id": "SaveContent",
                    "Title": "Save the bat files as json",
                    "Type": "BatEditor",
                    "Command": "~/bin/junk-store.sh Dos saveconfig"
                }
            ]
        }
    },
    "windows-config-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "DosConfigEditor",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Get the bat files as json",
                    "Type": "BatEditor",
                    "Command": "~/bin/junk-store.sh Dos getconfig"
                },
                {
                    "Id": "SaveContent",
                    "Title": "Save the bat files as json",
                    "Type": "BatEditor",
                    "Command": "~/bin/junk-store.sh Dos saveconfig"
                }
            ]
        }
    },
    "sidebar-page-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "SideBarPage",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Populate Store",
                    "Type": "GetContent",
                    "Command": "~/bin/get-json.sh sidebar-page-content"
                },
                {
                    "Id": "InitGeneral",
                    "Title": "Populate Store",
                    "Type": "Init",
                    "Command": "~/bin/get-json.sh settings-general-actions"
                },
                {
                    "Id": "InitAdvanced",
                    "Title": "Populate Store",
                    "Type": "Init",
                    "Command": "~/bin/get-json.sh settings-advanced-actions"
                },
                {
                    "Id": "InitAbout",
                    "Title": "Populate Store",
                    "Type": "Init",
                    "Command": "~/bin/get-json.sh settings-about-actions"
                }
            ]
        }
    },
    "sidebar-page-content": {
        "Type": "SideBarPage",
        "Content": {
            "Title": "Settings",
            "Tabs": [
                {"Title": "About", "ActionId": "InitAbout"},
                {"Title": "Advanced", "ActionId": "InitAdvanced"},
                {"Title": "General", "ActionId": "InitGeneral"}
            ]
        }
    },
    "settings-general-content": {"Type": "EpicLogin"},
    "settings-advanced-content": {
        "Type": "Html",
        "Content": "<h1>hello world</h1>"
    },
    "settings-about-content": {"Type": "Text", "Content": "Hello World!"},
    "settings-about-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "AboutActions",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Populate about page",
                    "Type": "GetContent",
                    "Command": "~/bin/get-json.sh settings-about-content"
                }
            ]
        }
    },
    "settings-general-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "AboutActions",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Populate about page",
                    "Type": "GetContent",
                    "Command": "~/bin/get-json.sh settings-general-content"
                }
            ]
        }
    },
    "settings-advanced-actions": {
        "Type": "ActionSet",
        "Content": {
            "SetName": "AboutActions",
            "Actions": [
                {
                    "Id": "GetContent",
                    "Title": "Populate about page",
                    "Type": "GetContent",
                    "Command": "~/bin/get-json.sh settings-advanced-content"
                }
            ]
        }
    }
}

# Check if an argument is provided
if len(sys.argv) < 2:
    print("Please provide an argument.")
    sys.exit(1)

# Get the argument from the command line
argument = sys.argv[1]

# Look up the JSON fragment based on the argument
if argument in json_fragments:
    json_fragment = json_fragments[argument]
    print(json.dumps(json_fragment))
else:
    print("Invalid argument.")
    sys.exit(1)
