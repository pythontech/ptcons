#!/bin/env python
#=======================================================================
#       Test Tk application
#=======================================================================
from twisted.internet import reactor, protocol, tksupport
from twisted.protocols import basic
from Tkinter import *
import urllib
from tupleprotocol import TupleProtocol

root = None
text = None

class XconsProtocol(TupleProtocol):
    def connectionMade(self):
        print 'Connected'

    def tupleReceived(self, tokens):
        print 'tuple: %r' % (tokens,)
        cmd = tokens[0]
        args = tokens[1:]
        if cmd == 'v':
            svrcan, clntmust = args
        elif cmd == 'c':
            # Connected to host
            host, pos = args
            root.wm_title('xcons: %s' % host)
            self.reply('r', 0, pos)
        elif cmd == 'o':
            # Output data
            pos, data = args
            text.insert('end', data)

    def reply(self, *args):
        self.sendTuple(args)

class XconsFactory(protocol.ClientFactory):
    protocol = XconsProtocol

    def clientConnectionFailed(self, connector, reason):
        print reason

root = Tk()

mbar = Frame(root)
mbar.pack(side=TOP, fill=X)
if mbar:
    mb_target = Menubutton(mbar, text='Target', underline=0)
    if mb_target:
        menu = mb_target['menu'] = Menu(mb_target)
        menu.add_command(label='Connect...', underline=0)
    mb_target.pack(side=LEFT)

text = Text(root)
text.pack(side=TOP, fill=BOTH)

# Link Tk into twisted main loop
tksupport.install(root)

reactor.connectTCP('localhost', 8183, XconsFactory())
reactor.run()
