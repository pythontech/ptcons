#!/bin/env python
#=======================================================================
#       Test Tk application
#=======================================================================
from twisted.internet import reactor, protocol, tksupport
from twisted.protocols import basic
from Tkinter import *
from tupleprotocol import TupleProtocol

i_support = []			# Extension features supported

class ConsProtocol(TupleProtocol):
    '''This handles the low-level protocol between client and server'''
    def __init__(self, session):
	self.session = session

    def connectionMade(self):
	'''Called when transport connected to server.
	We expect to receive a "v" message next in order to
	negotiate options supported by either side
	'''
	self.session.conn = self

    def connectionLost(self, reason):
	self.session.conn = None

    def tupleReceived(self, tokens):
        print 'tuple: %r' % (tokens,)
        cmd = tokens[0]
        args = tokens[1:]
        if cmd == 'v':
            svrcan, clntmust = args
	    unsupported = []
	    for feature in clntmust.split():
		if not feature in i_support:
		    unsupported.add(feature)
	    if unsupported:
		if self.session:
		    self.session.display.showError('Client does not support feature%s %s required by server' % ('s'[:len(unsupported) > 1], ','.join(unsupported)))
		reactor.stop()
	    else:
		# View the given host
		self.sendCommand('m', self.session.host)
        elif cmd == 'm':
            # Connected to host
            host, pos = args
            # root.wm_title('xcons: %s' % host)
	    self.session.display.setConnected(True, self.session.host)
	    self.session.positionReceived(pos)
        elif cmd == 'o':
            # Output data
            pos, data = args
	    self.session.display.outputDataReceived(pos, data)
	elif cmd == 'p':
	    # End position changed
	    pos, = args
	    self.session.positionReceived(pos)

    def sendCommand(self, *args):
        self.sendTuple(args)

class ConsSession(protocol.ClientFactory):
    '''This handles a session connecting to consd and monitoring
    the console for a particular host.
    '''
    def __init__(self, host, display):
	self.host = host
	self.display = display
	display.session = self
	self.conn = None		# ConsProtocol when connected
	self.lastpos = 0

    def start(self):
	'''Start connecting to consd'''
	reactor.connectTCP('localhost', 8183, self)

        #---------------------------------------------------------------------
	#	Methods for Factory interface
	#---------------------------------------------------------------------

    def buildProtocol(self, addr):
	prot = ConsProtocol(self)
	return prot

    def clientConnectionFailed(self, connector, reason):
	self.display.showError('Connection failed: %s' % reason)

	#---------------------------------------------------------------------
	#	Methods called by Protocol
	#---------------------------------------------------------------------

    def positionReceived(self, pos):
	oldend = self.lastpos
	self.lastpos = pos
	# Assume we want all the output
	self.requestOutput(oldend, pos)

    def outputDataReceived(self, pos, data):
	self.display.outputDataReceived(pos, data)

	#---------------------------------------------------------------------
	#	Methods called by display
	#---------------------------------------------------------------------

    def requestOutput(self, beg, end):
	if self.conn:
	    self.conn.sendCommand('r', beg, end)

    def sendInput(self, input):
	if self.conn:
	    self.conn.sendCommand('i', input)

#-----------------------------------------------------------------------
#	Tk UI
#-----------------------------------------------------------------------
class XconsDisplay:
    def __init__(self):
	root = self.root = Tk()
	root.wm_title('xcons')
	# Link Tk into twisted main loop
	tksupport.install(root)

	# Create menu bar
	mbar = Frame(root)
	mbar.pack(side=TOP, fill=X)
	if mbar:
	    mb_console = Menubutton(mbar, text='Console', underline=0)
	    if mb_console:
		menu = mb_console['menu'] = Menu(mb_console, tearoff=0)
		# menu.add_command(label='Connect...', underline=0)
		menu.add_command(label='Exit', underline=1,
				 command=root.quit)
	    mb_console.pack(side=LEFT)

	status = self.status = Label(root)
	status.pack(side=BOTTOM, anchor=W)

	# Create text area
	#xsc = Scrollbar(root, orient=HORIZONTAL)
	ysc = Scrollbar(root)
	text = self.text = Text(root,
				font='jet-small-fixed',
				yscrollcommand=ysc.set)
	ysc.config(command=text.yview)

	ysc.pack(side=RIGHT, fill=Y)
	text.pack(side=TOP, fill=BOTH)

	text.bind('<KeyPress>', self.keypress)

    def keypress(self, event):
	'''Intercept keypresses to pass to server'''
	print 'KeyPress %r sym=%r code=%r' % \
	      (event.char, event.keysym, event.keycode)
	if event.char:
	    if 0x20 <= ord(event.char) <= 0x7e:
		self.session.sendInput(event.char)
		# Don't allow default event handler to process it
		return 'break'
	    elif event.char == '\r':
		self.session.sendInput('\r\n')
		return 'break'
	    elif event.keysym in ('BackSpace','Delete'):
		self.session.sendInput(event.char)
		return 'break'
	# else allow default handler to deal with it

    def setConnected(self, connected, host):
	title = 'xcons: %s' % (host,)
	if connected:
	    self.status.configure(text='Connected', background='green')
	else:
	    self.status.configure(text='Not connected', background='red')
	    title += ' (disconnected)'
	self.root.wm_title(title)

    def showError(self, error):
	print error

    def outputDataReceived(self, pos, data):
	# For the moment, assume always appending
	self.text.insert('end', data)
	self.text.see('end')

if __name__=='__main__':
    import sys
    if len(sys.argv) > 1:
	host = sys.argv[1]
    else:
	host = 'dummy'
    disp = XconsDisplay()
    session = ConsSession(host, disp)
    session.start()
    reactor.run()
