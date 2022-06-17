"""
Author: RedFantom
License: GNU GPLv3
Copyright (c) 2021 RedFantom

This file is part of nextcloud-deck-trello-bisync, a project to use
Python scripts and the Deck and Trello APIs to provide synchronization
between the two. See the included README file for details.
"""
from nextcloud import NextCloud, exceptions as nc_exceptions
import re
import yaml
import trello
import trello.exceptions

settings = {}

print("Welcome to Deck-Trello Bisync! Let's get started on your config.yml\n")
print("You will be asked for your Trello API credentials, Nextcloud app password\n"
      "as well as other information. These will be stored in PLAIN-TEXT on your\n"
      "server, so make sure to keep your config.yml file secure and set the\n"
      "least permissive permissions possible for your setup.\n\n"
      "All prompts will repeat until valid information is given.\n\n")

# Trello API Settings
settings["trello"] = {}
x = ""
while not re.match("^[a-f0-9]{32}", x):
    x = input("Trello API key: ")
settings["trello"]["key"] = x

x = input("Would you like to generate a link to get your Trello API secret? (y/n) [n]: ")
if x == "y":
    print("Open the following link in your browser:")
    print(f"https://trello.com/1/authorize?expiration=never&name=Nextcloud+Bisync&scope=read,write&response_type=token&key={settings['trello']['key']}")
    print("And paste your API secret into the next question.")

while not re.match("^[a-f0-9]{64}", x):
    x = input("Trello API secret: ")
settings["trello"]["secret"] = x

client = trello.TrelloClient(settings["trello"]["key"], settings["trello"]["secret"])
try:
    orgs = client.list_organizations()
    print("Successfully retrieved Trello workspaces.")
except trello.exceptions.Unauthorized:
    print("Validation of Trello API keys failed.")
    exit(1)

# Nextcloud API Settings
settings["nextcloud"] = {}
while not re.match("^https://([a-zA-Z0-9.]{2,})$", x):
    x = input("Nextcloud URL: ")
settings["nextcloud"]["url"] = x

x = ","
while not re.match("^[a-zA-Z0-9]+$", x):
    x = input("Nextcloud Username: ")
settings["nextcloud"]["username"] = x

x = ""
while not re.match("^([a-zA-Z0-9]{5}-){4}[a-zA-Z0-9]{5}$", x):
    x = input("Nextcloud App Password: ")
settings["nextcloud"]["password"] = x
try:
    nc = NextCloud(
        settings["nextcloud"]["url"],
        user=settings["nextcloud"]["username"],
        password=settings["nextcloud"]["password"])
    users = nc.get_users()
    users = users.data["users"]
    print("Successfully retrieved Nextcloud user list.")
except nc_exceptions.NextCloudLoginError:
    print("Failed to verify Nextcloud credentials.")
    exit(2)
print()

# Synchronization Settings
print("Now it's time for you to select what workspaces to synchronize.")
print("The following workspaces have been found:")
print("- Default, user boards (default)")
for org in orgs:
    print(f"- {org.name} ({org.id})")

settings["workspaces"] = {}
print()
print("Because Deck lacks workspaces, Workspaces will be marked by board\n"
      "prefixes. You'll be able to choose the prefix you want for each \n"
      "workspace you choose to synchronize.\n"
      "Now, enter a workspace ID (the value between brackets) to configure\n"
      "it for synchronization. When done, just enter 'done'.\n\n")

x = ""
while True:
    x = input("Workspace ID: ")
    if x == "done":
        break
    if x not in ["default"] + [org.id for org in orgs]:
        continue

    if x in [org.id for org in orgs]:
        org = [org for org in orgs if org.id == x][0]
        prefix = org.id
    else:
        org = None
        prefix = "Trello"

    x = input(f"Choose a board prefix, enter . for no prefix: [{prefix}]: ")
    if x == ".":
        prefix = ""
    elif x == "":
        pass
    else:
        prefix = x
    settings["workspaces"][org.id if org is not None else "default"] = prefix

# Users
print("If you want the assigning of users to certain cards to work correctly,\n"
      "every Trello user in each workspace must be mapped to a Nextcloud user.\n")

x = input("Do you want to set this up right now? (y/n) [y]: ")
print("Enter the Nextcloud username for each Trello username. Enter 'skip' to\n"
      "ignore this Trello user.")
if x != "n":
    settings["users"] = {}
    for org in settings["workspaces"]:
        if org == "default":
            continue
        org = [o for o in orgs if o.id == org][0]
        members = org.get_members()
        for member in members:
            while True:
                name = input(f"Nextcloud username for '{member.username}': ")
                if name == "skip":
                    break
                elif name in users:
                    users.remove(name)
                else:
                    print("Unavailable username selected")
                    continue
                settings["users"][member.username] = name
                break


with open("config.yml", "w") as fo:
    yaml.dump(settings, fo)

print("Thank you! Your config file will be saved to './config.yml'.")
print("cron.py depends on your `config.yml` file as well as the .db file.\n"
      "Keep them both safe to ensure you don't end up with wonky boards.")
