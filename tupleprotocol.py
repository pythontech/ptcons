#=======================================================================
#	$Id$
#	Protocol handler allowing tuples of strings or integers to be
#	passed between client and server.
#	Each tuple is represented as a line of text; integer encoded as
#	'i' plus decimal representation, string as 's' plus URL-encoded
#	bytes; items space-separated
#=======================================================================
from twisted.protocols import basic

import urllib

def encode(val):
    if isinstance(val,str):
        return 's' + urllib.quote(val)
    elif isinstance(val,int):
        return 'i%d' % val
    else:
        raise ValueError, 'Only int or string may be encoded'

def decode(val):
    if val[0] == 's':
        return urllib.unquote(val[1:])
    elif val[0] == 'i':
        return int(val[1:])
    else:
        return ValueError, 'Unknown type %r' % val[0]

class TupleProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        values = map(decode, line.split())
        self.tupleReceived(values)

    def sendTuple(self, values):
        line = ' '.join(map(encode, values))
        self.sendLine(line)

    def sendValues(self, *values):
	self.sendTuple(values)
