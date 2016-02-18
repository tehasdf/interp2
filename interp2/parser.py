from interp2.compiler import Compiler
from interp2.interp import Interp


class ParsleyCompatibleParser(object):
    def __init__(self, grammar, receiver, bindings):
        self._grammar = grammar
        self._receiver = receiver
        self._bindings = bindings
        self._bindings['receiver'] = receiver

        self.compiler = Compiler(self._grammar)
        self._rules = {}
        self._setup()


    def getParseTree(self, name):
        # XXX this must also cache .compileRule, not just .getRule
        # but apparently some state is still held inside the parse tree?
        if name not in self._rules:
            self._rules[name] = self.compiler.getRule(name)
        return self.compiler.compileRule(self._rules[name])

    def _setup(self):
        parseTree = self.getParseTree(self._receiver.currentRule)
        self._interp = Interp(parseTree, self._setup, names=self._bindings)

    def receive(self, data):
        self._interp.receive(data)
