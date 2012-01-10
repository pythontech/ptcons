#!/bin/env python
#=======================================================================
#       Console daemon
#=======================================================================
from twisted.internet import protocol, reactor, error
from twisted.protocols import basic
from twisted.conch import telnet
from tupleprotocol import TupleProtocol
import hist

# Port for client commands
CMDPORT = 8183

# Monitor states
CONNECTED = 'connected'
CONNECTING = 'connecting'
DISCONNECTED = 'disconnected'

def optionDesc(opt):
    desc = {'\x01':'Echo',
	    '\x03':'Suppress Go Ahead',
	    '\x18':'Terminal Type',
	    }.get(opt)
    if desc:
	return '%r (%s)' % (opt, desc)
    else:
	return repr(opt)

class ConsoleMonitor:
    '''One instance of this handles a single VCP port.
    A connection is attempted on start-up, then whenever
    connection is lost.
    It keeps a history of console output.
    Several clients may be connected at a time.  Updates of the end
    position are broadcast to all clients; they may in turn request
    the new data.
    '''
    def __init__(self, host, vcp, port):
        # Configuration
        self.host = host
        self.vcp = vcp
        self.port = port
        # State
        self.history = hist.History()
	self.position = len(self.history)
        self.clients = {}       # id -> client

    def start(self):
        self.startConnecting()

    def addClient(self, client):
        self.clients[id(client)] = client

    def removeClient(self, client):
        if id(client) in self.clients:
            del self.clients[id(client)]

    def getPosition(self):
	return self.position

    def getData(self, beg, end):
	if beg < 0 or end > len(self.history):
	    raise ValueError, 'Invalid range'
	data = self.history[beg:end]
	return data

    def broadcastPosition(self, pos):
        for clnt in self.clients.values():
            clnt.sendPosition(pos)

    def startConnecting(self):
	self.state = CONNECTING
	print 'Connecting to %s:%d' % (self.vcp, self.port)
	reactor.connectTCP(self.vcp, self.port,
			   factory=ConsoleFactory(self))

    def sendInput(self, data):
	if self.state == CONNECTED:
	    self.protocol.transport.write(data)
        
    def appendData(self, data):
	'''New data ahas arrived from the console.
	Add to the history buffer and broadcast to any interested clients.
	'''
        if not data:
            return
        self.history.add(data)
        self.position = len(self.history)
        self.broadcastPosition(self.position)

#-----------------------------------------------------------------------
#	Handle back-end connection to a VCP port
#-----------------------------------------------------------------------
class ConsoleProtocol(telnet.TelnetTransport):
    '''Handler for a connection to the VCP'''
    def __init__(self, monitor):
	telnet.TelnetTransport.__init__(self)
        self.monitor = monitor

    def connectionMade(self):
        self.monitor.state = CONNECTED
	self.monitor.protocol = self

    def enableLocal(self, option):
	'''Peer is suggesting we enable an option (DO xxx)'''
	print 'enableLocal %s' % optionDesc(option)
	return False

    def enableRemote(self, option):
	'''Peer is sugegsting it will enable an option (WILL xxx)'''
	print 'enableRemote %s' % optionDesc(option)
	return False

    def applicationDataReceived(self, data):
	print 'data received %r' % data
        self.monitor.appendData(data)

    def connectionLost(self, reason):
	print 'connection lost %r' % reason
        self.monitor.state = DISCONNECTED

class ConsoleFactory(protocol.ClientFactory):
    def __init__(self, monitor):
        self.monitor = monitor

    def buildProtocol(self, addr):
        prot = ConsoleProtocol(self.monitor)
        prot.factory = self
        return prot

    def clientConnectionFailed(self, connector, reason):
	print 'connection failed: %r' % reason

#-----------------------------------------------------------------------
#	Handle front end connections from clients
#-----------------------------------------------------------------------
class CommandProtocol(TupleProtocol):
    '''Handler for a connection from a client'''

    def __init__(self, app):
	self.app = app
	self.monitor = None		# No target console yet

    def connectionMade(self):
        print 'connection from %s' % self.transport.getPeer()
        self.sendTuple(('v', '', ''))
        # self.sendTuple(('c', 'localhost', len(buffer)))

    def tupleReceived(self, tokens):
        print 'tuple: %r' % (tokens,)
        cmd = tokens[0]
        args = tokens[1:]
	if cmd == 'eval':
	    # Dangerous debug tool
	    try:
		res = eval(' '.join(args))
	    except Exception, e:
		res = str(e)
	    self.reply('eval', res)
	elif cmd == 'quit':
	    self.transport.loseConnection()
	elif cmd == 'm':
	    host, = args
	    print 'monitor %s' % host
	    if host not in self.app.monitors:
		self.error('host %s not being monitored' % host)
	    else:
		self.monitor = self.app.monitors[host]
		self.monitor.addClient(self)
		pos = self.monitor.getPosition()
		self.reply('m', host, pos)
        elif cmd == 'i':
            data, = args
            print 'input %r' % data
	    if not self.monitor:
		self.error('No monitoring any console')
	    else:
		self.monitor.sendInput(data)
        elif cmd == 'r':
            beg, end = map(int, args)
	    if not self.monitor:
		self.error('No monitoring any console')
	    data = self.monitor.getData(beg, end)
	    self.reply('o', beg, data)
        else:
            self.error('Unknown command %r' % cmd)

    def sendPosition(self, pos):
	self.reply('p', pos)

    def connectionLost(self, reason):
        print 'Client %s disconnected' % self.transport.getPeer()
	if self.monitor:
	    self.monitor.removeClient(self)
	    self.monitor = None

    def error(self, err):
        self.reply('e', err)

    def reply(self, *args):
        self.sendTuple(args)

class CommandFactory(protocol.ServerFactory):
    def __init__(self, app):
	self.app = app

    def buildProtocol(self, addr):
	return CommandProtocol(self.app)


#-----------------------------------------------------------------------
#	Application managing several consoles
#-----------------------------------------------------------------------
class ConsdApplication:
    def __init__(self):
	self.monitors = {}		# host -> ConsoleMonitor

    def addMonitor(self, host, vcp, port):
        monitor = ConsoleMonitor(host, vcp, port)
        self.monitors[host] = monitor

    def readConfiguration(self, filename):
	for line in open(opts.configfile):
	    if line.startswith('#'):
		continue
	    tokens = line.split()
	    if not tokens:
		continue
	    if tokens[0] == 'console':
		host, vcp, port = tokens[1:4]
		self.addMonitor(host, vcp, int(port))
	    else:
		raise ValueError, 'Unknown configuration directive %r' % (tokens[0],)

    def run(self):
	reactor.listenTCP(CMDPORT, CommandFactory(self))
	for mon in self.monitors.values():
	    mon.start()
	reactor.run()

if __name__=='__main__':
    import sys
    from optparse import OptionParser, make_option
    op = OptionParser(usage='usage: %prog [options]')
    op.add_option('-c','--config', dest='configfile',
		  help='configuration file')
    # op.set_defaults(verbose=False, trace_level=0)
    (opts, args) = op.parse_args()
    if not opts.configfile:
	print >>sys.stderr, 'No config file'
	sys.exit(2)

    app = ConsdApplication()
    app.readConfiguration(opts.configfile)

    app.run()
