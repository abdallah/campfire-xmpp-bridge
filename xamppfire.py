import pyfire
import logging
import sys
from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout
from settings import *

logging.basicConfig(level=logging.ERROR)


class JBot(ClientXMPP):
    
    def __init__(self, jid, password, campfire_room):
        ClientXMPP.__init__(self, jid, password)
        self.room = JABBER_ROOM
        self.nick = JABBER_NICKNAME
        self.campfire_room = campfire_room
        
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.xmpp_incoming)
        self.add_event_handler("muc::%s::got_online" % self.room,
                               self.muc_online)

        
    def start(self, event):
        self.get_roster()
        self.send_presence()
        
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        wait=True)
        
    def xmpp_incoming(self, msg):
        print msg
        if msg['mucnick'] != self.nick and self.nick in msg['body']:
            self.to_campfire(msg)
            
    def from_campfire(self, message):
        username = ""
        msg = ""
        if message.user:
            username = message.user.name
        
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
            
        if username!=CAMPFIRE_NICKNAME:
            print 'No user, message: %s' % msg
            self.send_message(mto=JABBER_ROOM,
                              mbody=msg,
                              mtype='groupchat')


    def to_campfire(self, message):
        msg = message['body']
        sender = message['mucnick']
        self.campfire_room.speak('[%s]: %s' % (sender, msg))



def error(e):
    print("Stream STOPPED due to ERROR: %s" % e)
    sys.exit(2)
                    
if __name__ == '__main__':
    # start campfire stream thread
    campfire = pyfire.Campfire(CAMPFIRE_ACCOUNT, CAMPFIRE_USERNAME, CAMPFIRE_PASSWORD, ssl=True)
    campfire_room = campfire.get_room_by_name(CAMPFIRE_ROOM)
    campfire_room.join()
    stream = campfire_room.get_stream(error_callback=error)
    print "Campfire thread started"

    # start XMPP stream thread
    xmpp = JBot(JABBER_USERNAME, JABBER_PASSWORD, campfire_room)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    xmpp.register_plugin('xep_0199') # XMPP Ping
    # add ('74.50.61.85', '5222') if connect doesn't work
    if xmpp.connect(JABBER_SERVER):
        xmpp.process(block=False)
        print "Jabber thread started"
    else: 
        print "Unable to connect"
        sys.exit(1)
        
    # and attach the campfire stream thread to XMPP
    stream.attach(xmpp.from_campfire).start()
