from interp2.compiler import Compiler
from interp2.interp import Interp


class ParsleyCompatibleParser(object):
    def __init__(self, grammar, receiver, bindings):
        self._grammar = grammar
        self._receiver = receiver
        self._bindings = bindings
        self._bindings['receiver'] = receiver

        self._setup()

    def _setup(self):
        compiler = Compiler(self._grammar)
        rule = compiler.getRule(self._receiver.currentRule)
        parseTree = compiler.compileRule(rule)
        self._interp = Interp(parseTree, self._setup, names=self._bindings)

    def receive(self, data):
        self._interp.receive(data)
