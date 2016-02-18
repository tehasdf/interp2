from interp2.compiler import Compiler
from interp2.interp import Interp

netstringsGrammar = """
nonzeroDigit = digit:x ?(x != '0')
digits = <'0' | nonzeroDigit digit*>:i -> int(i)

netstring = digits:length ':' <anything{length}>:string ',' -> string
receiveNetstring = netstring:string -> receiver.netstringReceived(string)
"""


class NetstringsReceiver(object):
    def __init__(self):
        self.strings = []

    def netstringReceived(self, string):
        self.strings.append(string)


class TestInterp(object):
    def test_reuseParseTree(self):
        receiver = NetstringsReceiver()

        compiler = Compiler(netstringsGrammar)
        rule = compiler.getRule('receiveNetstring')
        parseTree = compiler.compileRule(rule)

        interp = Interp(parseTree, names={'receiver': receiver})
        interp.receive('3:aaa,')
        assert receiver.strings == ['aaa']
        parseTree = compiler.compileRule(rule)
        interp = Interp(parseTree, names={'receiver': receiver})
        interp.receive('2:bb,')

        assert receiver.strings == ['aaa', 'bb']