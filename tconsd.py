#!/bin/env python
#=======================================================================
#       Demo server
#=======================================================================
from twisted.internet import protocol, reactor
from twisted.protocols import basic
import urllib
from tupleprotocol import TupleProtocol

buffer = '\n'.join(map(str, range(12345, 12500)))

conns = {}

class ConsProtocol(TupleProtocol):
    '''Handler for a connection from a client'''
    def connectionMade(self):
	conns[id(self)] = self
        print 'connection from %s' % self.transport.getPeer()
        self.sendTuple(('v', '', ''))
        self.sendTuple(('c', 'localhost', len(buffer)))

    def tupleReceived(self, tokens):
        print 'tuple: %r' % (tokens,)
        cmd = tokens[0]
        args = tokens[1:]
        if cmd == 'i':
            data, = args
            print 'input %r' % data
        elif cmd == 'r':
            beg, end = map(int, args)
            if beg < 0 or end > len(buffer):
                self.error('Invalid range')
            elif end > beg:
                data = buffer[beg:end]
                self.reply('o', beg, data)
        else:
            self.error('Unknown command %r' % cmd)

    def connectionLost(self, reason):
        print 'Client %s disconnected' % self.transport.getPeer()
	del conns[id(self)]

    def error(self, err):
        self.reply('e', err)

    def reply(self, *args):
        self.sendTuple(args)

class ConsFactory(protocol.ServerFactory):
    protocol = ConsProtocol

def newData():
    global buffer, conns
    # Add some new data
    data = str(len(buffer)) + '\n'
    buffer += data
    # Broadcast new size to client(s)
    for prot in conns.values():
	prot.reply('p', len(buffer))
    reactor.callLater(10, newData)
    
reactor.listenTCP(8183, ConsFactory())
reactor.callLater(10, newData)
reactor.run()
