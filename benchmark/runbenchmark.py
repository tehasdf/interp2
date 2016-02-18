from datetime import datetime
from twisted.test.proto_helpers import StringTransport
from parsley import makeProtocol


from interp2.compiler import Compiler
from interp2.interp import Interp
from interp2.protocol import makeProtocol as makeInterp2Protocol


def makeShortAndSimple():
    for num in range(20):
        for length in range(3, 6):
            yield '%d:%s,' % (length, 'a' * length)

def makeManyShort():
    for num in range(1000):
        yield '30:%s,' % ('a' * 30, )


def makeLong():
    for num in range(20):
        for length in [1025, 2049, 16385]:
            yield '%d:%s,' % (length, 'a' * length)

def makeManyLong():
    for num in range(100):
        yield '16385:%s,' % ('a' * 16385, )

TESTS = [
    ('short and simple', list(makeShortAndSimple())),
    ('many short messages', list(makeManyShort())),
    ('long messages', list(makeLong())),
    ('many long messages', list(makeManyLong())),
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


if __name__ == '__main__':
    for name, impl in [('parsley', parsleyTests), ('interp2', interp2Tests)]:
        for test_name, messages in TESTS:
            start_time = datetime.now()
            impl(messages)
            took = datetime.now() - start_time
            print '%s %s took %s' % (name, test_name, took)
