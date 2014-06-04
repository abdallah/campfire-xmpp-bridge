#!/usr/bin/python
import pyfire
import logging
import sys
from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout
from settings import *
import threading

logging.basicConfig(level=logging.ERROR, 
                    format='(%(threadName)-10s) %(message)s')


class JBot(ClientXMPP):
    
    def __init__(self, jid, password, campfire_room):
        ClientXMPP.__init__(self, jid, password)
        self.room = JABBER_ROOM
        self.nick = JABBER_NICKNAME
        self.answer_to = JABBER_NICKNAMES
        self.campfire_room = campfire_room
        
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.xmpp_incoming)
        
    def start(self, event):
        self.get_roster()
        self.send_presence()
        
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        wait=True)
        
    def check_nick(self, msg):
        nick_called = msg.split(' ', 1)[0][1:]
        if nick_called.lower() in map(str.lower, BOT_NICKNAMES):
            self.nick_called = nick_called
        else:
            self.nick_called = None
        return self.nick_called
        
    def xmpp_incoming(self, msg):
        logging.debug('mucnick: %s'%msg['mucnick'])
        logging.debug('body: %s'%msg['body'])
        logging.debug('nick_called: %s'%self.check_nick(msg['body']))
        if msg['mucnick'] != self.nick \
            and msg['body'][0] in BOT_PREFIX \
            and self.check_nick(msg['body']):
            if '+die' in msg['body']:
                self.leave()
            elif '+who' in msg['body']:
                self.get_campfire_users()
            elif '+recent' in msg['body']:
                self.get_campfire_recent()
            elif '+reload' in msg['body']:
                self.reconnect()
            elif '+help' in msg['body']:
                self.help_message()
            else:
                msg['body'] = msg['body'][len(self.nick_called)+1:]
                self.to_campfire(msg)

    def leave(self):
        self.disconnect(wait=True)
            
    def from_campfire(self, message):
        username = ""
        msg = ""
        if message.user:
            username = message.user.name
            logging.info("%s" % message.user.get_data())
        
        if message.is_joining():
            msg = "--> %s ENTERS THE ROOM" % username
        elif message.is_leaving():
            msg = "<-- %s LEFT THE ROOM" % username
        elif message.is_text():
            msg = "[%s] %s" % (username, message.body)
        elif message.is_upload():
            msg = "-- %s UPLOADED FILE %s: %s" % (username, message.upload["name"],
                message.upload["url"])
        elif message.is_topic_change():
            msg = "-- %s CHANGED TOPIC TO '%s'" % (username, message.body)
            
        if message.user:
            if message.user.email_address!=CAMPFIRE_EMAIL:
                self.to_xmpp(msg)

    def to_xmpp(self, message):
        self.send_message(mto=JABBER_ROOM,
                          mbody=message,
                          mtype='groupchat')

    def to_campfire(self, message):
        msg = message['body']
        sender = message['mucnick']
        self.campfire_room.speak('[%s]: %s' % (sender, msg))

    def get_campfire_users(self):
        users = self.campfire_room.get_users()
        usernames = [u['name'] for u in users]
        msg = "The following people are currently in the chatroom: %s" % ', '.join(usernames)
        self.to_xmpp(msg)

    def get_campfire_recent(self, limit=None):
        messages = self.campfire_room.recent(limit=limit)
        for msg in messages:
            self.from_campfire(msg)

    def reconnect(self):
        super(JBot, self).reconnect()
        self.campfire_room.leave()
        self.campfire_room.join()
        self.campfire_room.speak('Back. Ready for any requests you may have.')

    def help_message(self):
        msg = "* Send a message to the Campfire room by preceding it with @%s\n" % JABBER_NICKNAME
        msg += "* @%s +who to list users currently in the Campfire room\n" % JABBER_NICKNAME
        msg += "* @%s +recent to list recent messages from the Campfire room\n" % JABBER_NICKNAME
        self.to_xmpp(msg)

def error(e, room):
    logging.debug("Stream STOPPED due to ERROR: %s" % e)
    room.leave()
                    
if __name__ == '__main__':
    # start campfire stream thread
    campfire = pyfire.Campfire(CAMPFIRE_ACCOUNT, CAMPFIRE_USERNAME, CAMPFIRE_PASSWORD, ssl=True)
    campfire_room = campfire.get_room_by_name(CAMPFIRE_ROOM)
    campfire_room.join()
    campfire_room.speak('Back. Ready for any requests you may have.')
    stream = campfire_room.get_stream(error_callback=error)
    stream.daemon = True
    logging.info("%s" % "Campfire thread started")

    # start XMPP stream thread
    xmpp = JBot(JABBER_USERNAME, JABBER_PASSWORD, campfire_room)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    xmpp.register_plugin('xep_0199') # XMPP Ping
    if xmpp.connect(JABBER_SERVER):
        logging.info("%s" %  "Jabber connected started")
        # and attach the campfire stream thread to XMPP
        stream.attach(xmpp.from_campfire).start()
        xmpp.process(block=True)
    else: 
        logging.error("%s" % "Unable to connect")
        sys.exit(1)
        
