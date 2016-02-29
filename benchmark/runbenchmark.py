from datetime import datetime
from twisted.test.proto_helpers import StringTransport
from parsley import makeProtocol


from interp2.compiler import Compiler
from interp2.interp import Interp
from interp2.protocol import makeProtocol as makeInterp2Protocol


def makeShortAndSimple(scale):
    for num in range(20 * scale):
        for length in range(3, 6):
            yield '%d:%s,' % (length, 'a' * length)

def makeManyShort(scale):
    for num in range(1000 * scale):
        yield '30:%s,' % ('a' * 30, )


def makeLong(scale):
    for num in range(20 * scale):
        for length in [1025, 2049, 16385]:
            yield '%d:%s,' % (length, 'a' * length)

def makeManyLong(scale):
    for num in range(100 * scale):
        yield '16385:%s,' % ('a' * 16385, )

TESTS = [
    ('short and simple', makeShortAndSimple),
    ('many short messages', makeManyShort),
    ('long messages', makeLong),
    ('many long messages', makeManyLong),
]


grammarSource = """
nonzeroDigit = digit:x ?(x != '0')
digits = <'0' | nonzeroDigit digit*>:i -> int(i)

netstring = digits:length ':' <anything{length}>:string ',' -> string
receiveNetstring = netstring:string -> receiver.netstringReceived(string)
"""

class Receiver(object):
    currentRule = 'receiveNetstring'
    def __init__(self, sender):
        self._sender = sender

    def netstringReceived(self, netstring):
        pass

    def prepareParsing(self, proto):
        pass

    def finishParsing(self, reason):
        pass

class Sender(object):
    def __init__(self, transport):
        self._transport = transport

def parsleyTests(messages):
    NetstringProtocol = makeProtocol(grammarSource, Sender, Receiver)
    proto = NetstringProtocol()
    transport = StringTransport()
    proto.makeConnection(transport)
    for message in messages:
        proto.dataReceived(message)


def interp2Tests(messages):
    NetstringProtocol = makeInterp2Protocol(grammarSource, Sender, Receiver)
    proto = NetstringProtocol()
    transport = StringTransport()
    proto.makeConnection(transport)
    for message in messages:
        proto.dataReceived(message)


def twistedTests(messages):
    from twisted.protocols.basic import NetstringReceiver
    class Proto(NetstringReceiver):
        def stringReceived(self, string):
            pass

    proto = Proto()
    transport = StringTransport()
    proto.makeConnection(transport)
    for message in messages:
        proto.dataReceived(message)


if __name__ == '__main__':
    scale = 1
    NUMTESTS = 2
    for name, impl in [
                ('parsley', parsleyTests),
                ('interp2', interp2Tests),
                ('twisted', twistedTests)
            ]:

        for test_name, messagesFactory in TESTS:
            for num in range(NUMTESTS):
                messages = messagesFactory(scale)
                start_time = datetime.now()
                impl(messages)
                took = datetime.now() - start_time
                print '%s %s took %s' % (name, test_name, took)
            print
