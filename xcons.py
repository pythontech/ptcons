#!/bin/env python
#=======================================================================
#       Test Tk application
#=======================================================================
from twisted.internet import reactor, protocol, tksupport
from twisted.protocols import basic
from Tkinter import *
import urllib
from tupleprotocol import TupleProtocol

isupport = []			# Extension features supported

root = None
text = None
lastend = 0

class XconsProtocol(TupleProtocol):

    def connectionMade(self):
        print 'Connected'

    def tupleReceived(self, tokens):
	global lastend
        print 'tuple: %r' % (tokens,)
        cmd = tokens[0]
        args = tokens[1:]
        if cmd == 'v':
            svrcan, clntmust = args
	    compatible = True
	    for feature in clntmust.split():
		if not feature in isupport:
		    print 'Client does not support feature %s required by server' % feature
		    compatible = False
	    if not compatible:
		reactor.stop()
	    self.reply('m', 'vx_test-17')
        elif cmd == 'm':
            # Connected to host
            host, pos = args
            root.wm_title('xcons: %s' % host)
	    lastend = pos
            self.reply('r', 0, pos)
        elif cmd == 'o':
            # Output data
            pos, data = args
            text.insert('end', data)
	elif cmd == 'p':
	    # End position changed
	    pos, = args
	    self.reply('r', lastend, pos)
	    lastend = pos

    def reply(self, *args):
        self.sendTuple(args)

class XconsFactory(protocol.ClientFactory):
    protocol = XconsProtocol

    def clientConnectionFailed(self, connector, reason):
        print reason

#-----------------------------------------------------------------------
#	Create UI
#-----------------------------------------------------------------------
root = Tk()
root.wm_title('xcons')

mbar = Frame(root)
mbar.pack(side=TOP, fill=X)
if mbar:
    mb_target = Menubutton(mbar, text='Target', underline=0)
    if mb_target:
        menu = mb_target['menu'] = Menu(mb_target, tearoff=0)
        menu.add_command(label='Connect...', underline=0)
    mb_target.pack(side=LEFT)

#xsc = Scrollbar(root, orient=HORIZONTAL)
ysc = Scrollbar(root)
text = Text(root,
	    yscrollcommand=ysc.set)
ysc.config(command=text.yview)

ysc.pack(side=RIGHT, fill=Y)
text.pack(side=TOP, fill=BOTH)

# Intercept key presses
def keypress(event):
    print "KeyPress %r" % (event.char,)
    if event.char.isalpha():
	# Don't allow default event handler to process it
	return "break"

text.bind('<KeyPress>', keypress)

# Link Tk into twisted main loop
tksupport.install(root)

reactor.connectTCP('localhost', 8183, XconsFactory())
reactor.run()
