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
    def test_reuseParseTree_newInterp(self):
        receiver = NetstringsReceiver()

        compiler = Compiler(netstringsGrammar)
        rule = compiler.getRule('receiveNetstring')
        parseTree = compiler.compileRule(rule)

        interp = Interp(parseTree, names={'receiver': receiver})
        interp.receive('11:aaaaaaaaaaa,')
        assert receiver.strings == ['aaaaaaaaaaa']
        interp = Interp(parseTree, names={'receiver': receiver})
        interp.receive('2:bb,')

        assert receiver.strings == ['aaaaaaaaaaa', 'bb']

    def test_reuseMany(self):
        receiver = NetstringsReceiver()

        compiler = Compiler("""
            a = 'a'*:string 'b' -> receiver.netstringReceived(string)
        """)
        rule = compiler.getRule('a')
        parseTree = compiler.compileRule(rule)
        interp = Interp(parseTree, names={'receiver': receiver})
        interp.receive('aab')
        assert receiver.strings == [['a', 'a']]
        interp = Interp(parseTree, names={'receiver': receiver})
        interp.receive('aaab')
        assert receiver.strings == [['a', 'a'], ['a', 'a', 'a']]
