campfire-xmpp-bridge
====================

Campfire to XMPP bridge

Requirements: 
-------------
* [PyFire]
* [SleekXMPP]

Usage:
------
Create and edit the settings.py file with the following contents: 
```python
CAMPFIRE_USERNAME = "bot@example.com"
CAMPFIRE_PASSWORD = "StrongPassword!"
CAMPFIRE_NICKNAME = "BotName"
CAMPFIRE_ACCOUNT  = "accountname" # the part before campfirenow.com, example accountname.campfirenow.com
CAMPFIRE_ROOM     = "roomname"

JABBER_USERNAME   = "bot@jabber.example.com"
JABBER_PASSWORD   = "StrongPasswordTwo?"
JABBER_ROOM       = "room@conference.jabber.example.com"
JABBER_NICKNAME   = "Bot"
JABBER_SERVER     = ('1.2.3.4', '5222') 
```

Then start the script using:
```sh
# start using:
python xamppfire.py
```
Sample init script is provided 

Bot commands:
-------------
The script will relay all messages sent to __@JABBER_NICKNAME__ in XMPP room to the Campfire room  
All the messages sent in the Campfire room will be relayed to the XMPP room.
+ +who: list Campfire users
+ +recent: list recent messages in Campfire room


[PyFire]:https://github.com/mariano/pyfire
[sleekxmpp]:https://github.com/fritzy/SleekXMPP
