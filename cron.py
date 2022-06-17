"""
Author: RedFantom
License: GNU GPLv3
Copyright (c) 2021 RedFantom

This file is part of nextcloud-deck-trello-bisync, a project to use
Python scripts and the Deck and Trello APIs to provide synchronization
between the two. See the included README file for details.
"""
from deck import api as deck
import os
import pickle
import trello
from typing import List
import yaml

# Step one: Read the config file and setup the clients
with open("config.yml", "r") as fi:
    settings = yaml.load(fi)

trello_client = trello.TrelloClient(
    settings["trello"]["key"], settings["trello"]["secret"])
deck_client = deck.NextCloudDeckAPI(
    settings["nextcloud"]["url"], (settings["nextcloud"]["username"], settings["nextcloud"]["password"]))

board: deck.Board = deck_client.get_boards()[0]
stack: deck.Stack = deck_client.get_stacks(board.id)[0]

if os.path.exists("links.db"):
    with open("links.db", "rb") as fi:
        links = pickle.load(fi)
else:
    links = {}

# For every workspace to be synchronized...
for org, prefix in settings["workspaces"].items():
    org = trello_client.get_organization(org)

    # Step two: Load the boards for Trello and ensure their existence in Deck
    boards = org.get_boards("")
    for board in boards:
        board: trello.Board
        if board.id not in links:
            links[board.id] = {"deck": None, "lists": {}, "labels": {}}
            r = deck_client.create_board(prefix + board.name)
            links[board.id]["deck"] = r.id
        else:
            # TODO: Ensure the board name is up-to-date
            # Currently no support is available in Deck API Lib
            pass
        lists = board.open_lists()
        for list in lists:
            # Step three: Load the lists for Trello Board and ensure their existence in Deck
            list: trello.List
            if list.id not in links[board.id]["lists"]:
                links[board.id]["lists"][list.id] = {"deck": None, "cards": {}}
                r: deck.Stack = deck_client.create_stack(links[board.id]["deck"], list.name)
                links[board.id]["lists"][list.id]["deck"] = r.id
            else:
                # TODO: Ensure the list name is up-to-date
                # Currently no support is available in the Deck API Lib
                pass

            # Step four: Load the cards for Trello List and ensure their existence in Deck
            cards: List[trello.Card] = list.list_cards("")
            all_cards = []
            for list_id, d in links[board.id]["lists"].items():
                all_cards.extend(links[board.id]["lists"][list_id]["cards"])
            for card in cards:
                created = False
                if card.id not in links[board.id]["lists"][list.id]["cards"] and card.id not in all_cards:
                    links[board.id]["lists"][list.id]["cards"][card.id] = {"deck": None}
                    r: deck.Card = deck_client.create_card(
                        links[board.id]["deck"],
                        links[board.id]["lists"][list.id]["deck"],
                        title=card.name,
                        description=card.description,
                        duedate=card.due_date.isoformat() if card.due_date != "" else "")
                    links[board.id]["lists"][list.id]["cards"][card.id]["deck"] = \
                        (links[board.id]["lists"][list.id]["deck"], r.id)
                    created = True

                elif card.id in all_cards:  # Card has been moved!
                    # Delete the original card, recreate it
                    deck_origin = all_cards[card.id]
                    list_target_trello = card.list_id
                    deck_card: deck.Card = deck_client.get_card(links[board.id]["deck"], *deck_origin)
                    # Find the location of the original card
                    list_deck_trello_map = {links[board.id]["lists"][trello_id]["deck"]: trello_id
                                            for trello_id in links[board.id]["lists"].keys()}
                    list_source_trello = list_deck_trello_map[deck_origin[0]]
                    r: deck.Card = deck_client.reorder_card(links[board.id]["deck"], links[board.id]["lists"][list_source_trello],
                                                 deck_origin[1], deck_card.order, links[board.id]["lists"][list_target_trello]["deck"])
                    del all_cards[card.id]
                    del links[board.id]["lists"][list_source_trello]["cards"][card.id]
                    links[board.id]["lists"][list_target_trello]["cards"][card.id] = {
                        "deck": (r.stack_id, r.id)
                    }

                if not created:  # Ensure the card is updated
                    r: deck.Card = deck_client.update_card(
                        links[board.id]["deck"],
                        links[board.id]["lists"][list.id]["deck"],
                        title=card.name,
                        description=card.description,
                        duedate=card.due_date.isoformat() if card.due_date != "" else "")

            # Step five: Load the cards from Deck and ensure they are all in Trello
            board_id, stack_id = links[board.id]["deck"], links[board.id]["lists"][list.id]["deck"]
            cards: List[deck.Card] = deck_client.get_cards_from_stack(board_id, stack_id)

            for card in cards:
                # TODO: Implement support for pushing cards from Deck to Trello
                pass


with open("links.db", "wb") as fo:
    pickle.dump(links, fo)
