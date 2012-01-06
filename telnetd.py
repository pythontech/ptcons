#!/bin/env python
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, Protocol
from twisted.conch.telnet import TelnetProtocol
from twisted.protocols.basic import LineReceiver

#class Telnetd(Protocol):
class Telnetd(LineReceiver, TelnetProtocol):
    def connectionMade(self):
        print 'Connection from %s' % self.transport.getPeer()
        self.transport.write('Hello\r\n')
        self.transport.write('-> ')
        self.lineReceived = self.telnet_CMD

    def telnet_CMD(self, line):
        if not line:
            pass
        elif line == 'pwd':
            self.sendLine('/home/vxworks')
        else:
            self.sendLine('unknown %s' % line)
        self.transport.write('-> ')

class TelnetdFactory(ServerFactory):
    protocol = Telnetd

reactor.listenTCP(8180, TelnetdFactory())
reactor.run()
