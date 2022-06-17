# Bi-directional Sync between Nextcloud's Deck and Trello
Do your friends or colleagues want to use Trello and do you dislike
logging into separate services as much as I do? Now you can synchronize
your Trello boards to your Nextcloud Deck.

Functionality includes matching Trello boards and cards to Deck boards 
and cards, selecting what boards to synchronize and matching Nextcloud
users to Trello users.

## Why is this not a Nextcloud app?
The main reason for not implementing this as a Nextcloud app or directly
into the Deck app is that when done that way, unrealistic expectations
of what is possible may be given. Particularly, I don't currently see 
a way for proper bi-directional synchronization in real-time without 
just re-implementing the Deck app as a frond-end for Trello. This seems
undesirable to me, as the whole purpose of Deck is that it is fully your
own.

The motivation for this project is to provide access to your Trello 
boards and cards from Nextcloud, purely for people who are to lazy or
find it too tedious to log into their Trello account every day.

Writing a full front-end app for Trello is out of scope for my purposes,
and I don't have time to take on such a project.

## How do I use this app?
First, set up a new virtual environment for Python on your server, of at
least Python 3.6. Then run the `configure.py` script to create your 
settings file. Lastly, create a cron-job for `cron.py` to start 
synchronizing your boards and cards.

## How does synchronization work?
The Trello boards are regarded as authoritative, to minimize any damage
the application can do in case something goes wrong. First the Trello
changes are fetched and put into Deck, and only then are changed and
added cards pushed from Deck to Trello. You can't create boards from 
Deck, only lists, cards and labels.

## Can I use these scripts with multiple users?
It's untested, but it should work. Just make sure that each workspace
is only synchronized by one user, and run multiple versions of the 
scripts each with their own config file.
