import os
import shutil
import time

import requests
import json

import urllib3

settings = {
    # the guild's id that you want to download.
    # THIS IS REQUIRED.
    "Guild_ID" :"GUILDIDHERE",

    # Your discord token
    # THIS IS REQUIRED.
    "Token": "TOKENHERE",

    # The save path that its going to save too
    # example: "C:\\USERNAME\\Desktop\\Discord"
    # Note: This will not be the root dir of the saving that will be in a folder-
    # named the guild's name within the Save_Path folder.
    # This will default too the current script directory if this is blank.
    "Save_Path": "",

    # Guild Settings
    "Guild": {
        # Saves the Info
        "Save_Info": True,

        # Saves the Channel List
        "Save_Channel_List": True,

        # Saves the Guild icon
        "Save_Guild_Icon": True,

        # Saves the GIF version of the icon if present
        "Save_Animated_Guild_Icon": True,

        # Saves the User List
        "Save_Users": True,

        # Saves all Guild Emojis
        "Save_Emojis": True,
    },

    # Channel Settings
    "Channels": {
        # Save all Channel Messages
        "Save_Messages": True,

        # Save all message attachments
        # Note: this can take a long time, if it's a big server.
        # this is heavily dependent on your internet speed.
        "Save_Attachments": False,

        # If enabled only saves the channel id's inside
        # the Channel_Whitelist list.
        "Save_only_Whitelist": True,

        # List of channels to only save if
        # Save_only_Whitelist is True
        "Channel_Whitelist": [

        ],

        # If True it will not save any channels that are
        # within the Channel_Blacklist list.
        "Dont_save_blacklisted": True,

        # List of channels to blacklist
        "Channel_Blacklist": [

        ],
    },

    # ONLY CHANGE THIS IS YOU KNOW WHAT YOUR DOING.
    # The api url might be changed in later versions of discord.
    "APIUrl": "https://discord.com/api/v8/",
}

# This is used by all api requests to discord.
headers = {
    "accept": "*/*",
    "authorization": settings["Token"]
}

def makeDir(path):
    if (not os.path.isdir(path)):
        os.mkdir(path)


def writeFiles(guildData, guildChannels, filepath):
    guildPath = filepath + "\\" + guildData["name"]
    makeDir(guildPath)
    makeDir(guildPath + "\\channels")
    makeDir(guildPath + "\\emojis")
    for channel in guildChannels:
        # Checks if this is a text channel or an announcement channel
        if channel['type'] == 0 or channel['type'] == 5:
            makeDir(guildPath + "\\channels\\" + channel['name'])
            makeDir(guildPath + "\\channels\\" + channel['name'] + "\\files")
    if settings["Guild"]["Save_Info"]:
        writeToFile(guildPath + "\\guild.json", json.dumps(guildData, sort_keys=True, indent=4))
    if settings["Guild"]["Save_Channel_List"]:
        writeToFile(guildPath + "\\channels.json", json.dumps(guildChannels, sort_keys=True, indent=4))
    if settings["Guild"]["Save_Guild_Icon"]:
        downloadIcon(guildPath, guildData)
    if settings["Guild"]["Save_Emojis"]:
        print("Downloading Emojis!")
        for emoji in guildData['emojis']:
            downloadEmoji(guildPath + "\\emojis", emoji)
    for channel in guildChannels:
        # Checks if it should even save this channel
        if settings["Channels"]["Save_only_Whitelist"] and\
                (not str(channel['id']) in str(settings["Channels"]["Channel_Whitelist"])):
            continue
        if settings["Channels"]["Dont_save_blacklisted"] and\
                str(channel['id']) in str(settings["Channels"]["Channel_Blacklist"]):
            continue
        # Checks if this is a text channel or an announcement channel
        if channel['type'] == 0 or channel['type'] == 5:
            print("Downloading " + channel['name'] + " channel!")
            downloadChannelMessages(channel['id'], guildPath + "\\channels\\" + channel['name'])



def clearTxtFile(filePath):
    if not os.path.isfile(filePath):
        open(filePath, "x").close()
    else:
        open(filePath, 'w').close()


def downloadIcon(filePath, guildData):
    print("Downloading Icon!")
    image_url = "https://cdn.discordapp.com/icons/" + guildData['id'] + "/" + str(guildData['icon']) + ".png?size=512"
    filename = filePath + "\\icon.png"
    downloadFile(filename, image_url)
    if "ANIMATED_ICON" in guildData['features']:
        print("Downloading Gif Icon!")
        image_url = "https://cdn.discordapp.com/icons/" + guildData['id'] + "/" + str(guildData['icon']) + ".gif?size=512"
        filename = filePath + "\\icon.gif"
        downloadFile(filename, image_url)


def downloadEmoji(filePath, emojiData):
    image_url = ""
    print("Downloading :" + emojiData['name'] + ":")
    if bool(emojiData['animated']):
        image_url = "https://cdn.discordapp.com/emojis/" + str(emojiData["id"]) + ".gif"
    else:
        image_url = "https://cdn.discordapp.com/emojis/" + str(emojiData["id"]) + ".png"
    filename = filePath + "\\" + image_url.split("/")[-1]
    downloadFile(filename, image_url)


def downloadFile(fileName, url):
    # This allows the internet to be disconnected-
    # and reconnected with out causing errors.
    while True:
        try:
            r = requests.get(url, stream=True)
            break
        except ConnectionAbortedError or urllib3.exceptions.ProtocolError:
            time.sleep(1)
    if r.status_code == 200:
        r.raw.decode_content = True
        with open(fileName, 'wb') as f:
            shutil.copyfileobj(r.raw, f)


def writeToFile(filepath, data, mode="w"):
    if not os.path.isfile(filepath):
        open(filepath, "x").close()
    fin = open(filepath, mode)
    fin.write(data);
    fin.close()


def downloadChannelMessages(channelId, outputPath):
    url = settings["APIUrl"] + "channels/" + channelId + "/messages"
    payload = {"limit": "100"}
    messageCount = 0
    # Prevents overwriting
    if settings["Channels"]["Save_Messages"]:
        clearTxtFile(outputPath + "\\messages.json")
    filesToDownload = []
    while True:
        r = []
        # This allows the internet to be disconnected-
        # and reconnected with out causing errors.
        while True:
            try:
                r = requests.get(url, params=payload, headers=headers)
                break
            except ConnectionAbortedError or urllib3.exceptions.ProtocolError:
                time.sleep(1)
        data = json.loads(r.text)
        # We don't have access to this channel so we can't read messages from it
        if "code" in data and data["code"] == str(50001):
            return
        if settings["Channels"]["Save_Attachments"]:
            for message in data:
                for attachment in message['attachments']:
                    if 'url' in attachment:
                        filesToDownload.append([attachment['id'], attachment['url']])
        if settings["Channels"]["Save_Messages"]:
            writeToFile(outputPath + "\\messages.json", r.text + "\n", "a")
        messageCount = messageCount + len(data)
        print("Fetching from Discord: " + str(messageCount) + " Messages | File Count: " + str(len(filesToDownload)), end='\r')
        if 0 <= 49 < len(data):
            payload["before"] = data[49]["id"]
        else:
            break
    print()
    if settings["Channels"]["Save_Attachments"]:
        count = len(filesToDownload)
        index = 0
        for attachment in filesToDownload:
            fileName = attachment[1].split("/")[-1]
            fileExtension = ""
            if "." in fileName:
                fileExtension = "." + fileName.split(".")[-1]
                fileName = attachment[1].split("/")[-1][0 :-(len(fileExtension))]
            downloadFile(outputPath + "\\files\\" + fileName + "_" + str(attachment[0]) + fileExtension, attachment[1])
            index = index + 1
            print("Downloading Files: " + str(index) + "/" + str(count) + " " +
                  str(float(index) / float(count) * 100) + "%", end='\r')
        if len(filesToDownload) > 0:
            print()


def getGuildData(guildId):
    r = []
    # This allows the internet to be disconnected-
    # and reconnected with out causing errors.
    while True:
        try:
            r = requests.get(settings["APIUrl"] + "guilds/" + guildId, headers=headers)
            break
        except ConnectionAbortedError or urllib3.exceptions.ProtocolError:
            time.sleep(1)
    return r.text


def getGuildChannels(guildId):
    r = []
    # This allows the internet to be disconnected-
    # and reconnected with out causing errors.
    while True:
        try:
            r = requests.get(settings["APIUrl"] + "guilds/" + guildId + "/channels", headers=headers)
            break
        except ConnectionAbortedError or urllib3.exceptions.ProtocolError:
            time.sleep(1)
    return r.text


# Start writing the file
writeFiles(
    # Get the guild data
    json.loads(getGuildData(settings["Guild_ID"])),
    # Get the channels
    json.loads(getGuildChannels(settings["Guild_ID"])),
    # Save path
    os.getcwd() if settings["Save_Path"] == "" else settings["Save_Path"]
)
