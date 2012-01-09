#!/bin/env python
#=======================================================================
#       Console daemon
#=======================================================================

# Monitor states
CONNECTED = 'connected'
CONNECTING = 'connecting'
DISCONNECTED = 'disconnected'

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
        self.clients = {}       # id -> client

    def start(self):
        self.startConnecting()

    def addClient(self, client):
        self.clients[id(client)] = client
        client.sendState(self.position)

    def removeClient(self, client):
        if id(client) in self.clients:
            del self.clients[id(client)]

    def broadcastPosition(self, pos):
        for clnt in self.clients.values():
            clnt.sendPosition(pos)

    def startConnecting(self):
        
    def appendData(self, data):
        if not data:
            return
        self.history. += data
        self.position = len(self.history)
        self.broadcastPosition(self.position)

class ConsoleProtocol(Protocol):
    '''Handler for a connection to the VCP'''
    def __init__(self, monitor):
        self.monitor = monitor

    def connectionMade(self):
        self.monitor.state = CONNECTED

    def dataReceived(self, data):
        self.monitor.appendData(data)

    def connectionLost(self, reason):
        self.monitor.state = DISCONNECTED

class ConsoleFactory(ClientFactory):
    def __init__(self, monitor):
        self.monitor = monitor

    def buildProtocol(self, addr):
        prot = ConsoleProtocol(self.monitor)
        prot.factory = self
        return prot

class ConsdApplication:
    def __init__(self):
        self.monitors = {}      # host -> ConsoleMonitor

    def addMonitor(self, host, vcp, port):
        monitor = ConsoleMonitor(host, vcp, port)
        self.monitors[host] = monitor
        monitor.start()
