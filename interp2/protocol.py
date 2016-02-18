from functools import partial
from ometa.grammar import OMeta
from ometa.protocol import ParserProtocol

from interp2.parser import ParsleyCompatibleParser

class Interp2ParserProtocol(ParserProtocol):
    def connectionMade(self):
        self.sender = self._senderFactory(self.transport)
        self.receiver = self._receiverFactory(self.sender)
        self.receiver.prepareParsing(self)
        self._parser = ParsleyCompatibleParser(
            self._grammar, self.receiver, self._bindings)


def makeProtocol(source, senderFactory, receiverFactory, bindings=None,
                 name='Grammar'):
    if bindings is None:
        bindings = {}
    return partial(
        Interp2ParserProtocol, source, senderFactory, receiverFactory, bindings)
