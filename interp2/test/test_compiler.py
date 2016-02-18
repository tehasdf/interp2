from ometa.interp import decomposeGrammar
from twisted.trial.unittest import TestCase
from ometa.grammar import OMeta
from parsley import makeGrammar

from interp2.compiler import Compiler, successExits
from interp2.matchers import anything, exact, Node, setRule, backtrack, setName, digit, noop, many
from interp2.interp import Interp, ParseError
from interp2.util import TestBase


def getParseTree(source, name=None):
    compiler = Compiler(source)
    return compiler.compileRule(compiler.getRule(name))


class TestCompiler(TestBase):
    def test_and(self):
        source = """
        a = 'b' 'c' 'de'
        """
        parseTree = getParseTree(source)
        self.assertMatch(parseTree, 'bcde')
        self.assertNoMatch(parseTree, 'bcd')

    def test_doubleand(self):
        source = """
        a = ('b' 'c') ('d' 'e')
        """
        parseTree = getParseTree(source)
        self.assertMatch(parseTree, 'bcde')


    def test_andor(self):
        source = """
        a = anything{1} ('b' | 'c')
        """
        parseTree = getParseTree(source)
        self.assertMatch(parseTree, 'ab')
        self.assertMatch(parseTree, 'ac')
        self.assertNoMatch(parseTree, 'ad')

    def test_orAnd(self):
        source = """
        a = ('b' | 'c') 'x'
        """
        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        result = i.receive('cx')
        self.assertEqual(i.rv, 'x')

    def test_nestedOr(self):
        source = """
        a = 'u'
            ('b'
                | (('c' 'x')
                    | ('z' ('f' | 'y') )
                    )
            )
            'a'
        """
        parseTree = getParseTree(source)
        self.assertMatch(parseTree, 'uba')
        self.assertMatch(parseTree, 'ucxa')
        self.assertMatch(parseTree, 'uzfa')
        self.assertMatch(parseTree, 'uzya')
        self.assertNoMatch(parseTree, 'ubya')

    def test_needsBacktracking(self):
        source = """
        a = ('a' 'b') | ('a' 'c') | 'z'
        """
        parseTree = getParseTree(source)
        self.assertMatch(parseTree, 'ab')
        self.assertNoMatch(parseTree, 'aa')
        self.assertMatch(parseTree, 'ac')
        self.assertMatch(parseTree, 'z')

    def test_moreBacktracking(self):
        source = """
        a = ('a' 'b' 'c' 'd' 'e' 'f') | ('a' 'b' 'c' 'd' 'e' 'z')
        """
        parseTree = getParseTree(source)
        self.assertMatch(parseTree, 'abcdez')

    def test_name(self):
        source = """
        a = anything{1}:x
        """
        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        i.receive('a')
        self.assertEqual(i.names['x'], 'a')

    def test_nameOr(self):
        source = """
        a = ('a' | 'b'):x
        """
        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        i.receive('b')
        self.assertEqual(i.names['x'], 'b')

    def test_relatedRule(self):
        source = """
        a = 'a'
        b = a 'b'
        """
        parseTree = getParseTree(source)
        self.assertMatch(parseTree, 'ab')

    def test_digit(self):
        source = "a = digit"
        parseTree = getParseTree(source)
        self.assertMatch(parseTree, '1')

    def test_conditional(self):
        source = "a = digit:x ?(x != '0')"
        parseTree = getParseTree(source)
        self.assertMatch(parseTree, '1')
        self.assertNoMatch(parseTree, 'a')

    def test_anyLength(self):
        source = "a = (digit*:y anything:x)"

        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        i.receive('12a')
        self.assertEqual(i.names['y'], ['1', '2'])
        self.assertEqual(i.names['x'], 'a')

    def test_manyOr(self):
        source = """
        a = (digit* 'x'):a | (digit* 'y'):a
        """
        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        i.receive('12y')
        self.assertEqual(i.names['a'], 'y')

    def test_consumedBy(self):
        source = """
        nonzeroDigit = digit:x ?(x != '0')
        digits = <'0' | digit*>:i
        """
        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        i.receive('12:')
        self.assertEqual(i.names['i'], '12')
        i = Interp(parseTree, None)
        i.receive('0')
        self.assertEqual(i.names['i'], '0')

    def test_consumedBy_double(self):
        source = """
        nonzeroDigit = digit:x ?(x != '0')
        digits = <'0' | digit*>:x ':' <'0' | digit*>:y -> int(x) - int(y)
        """
        parseTree = getParseTree(source, name='digits')
        i = Interp(parseTree, None)
        i.receive('12:34:')
        self.assertEqual(i.rv, 12 - 34)

    def test_netstrings(self):
        source = """
        nonzeroDigit = digit:x ?(x != '0')
        digits = <'0' | '1' '2' 'bar' |  nonzeroDigit digit*>:i -> int(i)
        netstring = digits:length ':' <anything{length}>:string ',' -> string
        """
        parseTree = getParseTree(source, name='netstring')
        i = Interp(parseTree, None)
        i.receive('3:asd,')
        self.assertEqual(i.rv, 'asd')

    def test_action(self):
        source = """
        a = anything:i -> int(i)
        """
        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        result = i.receive('1')
        self.assertEqual(i.rv, 1)

    def test_actionAnd(self):
        source = """
        a = <anything '5'>:i -> int(i)
        """
        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        result = i.receive('15')
        self.assertEqual(i.rv, 15)

    def test_actionOr(self):
        source = """
        a = ('0' | '5'):i -> int(i)
        """
        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        result = i.receive('5')
        self.assertEqual(i.rv, 5)

    def test_actionOnce(self):
        """
        The action is only called once, not more
        """
        source = """
        a = '0':i -> call(i)
        """
        _calls = []
        def cb(i):
            _calls.append(i)

        parseTree = getParseTree(source)
        i = Interp(parseTree, None)
        i.names['call'] = cb
        result = i.receive('0')
        self.assertEqual(_calls, ['0'])

    def test_callAfterOr(self):
        source = """
        foo = ('b' | 'a') 'b'
        receiveNetstring = foo:string -> cb(string)
        """
        _calls = []
        def cb(i):
            _calls.append(i)

        parseTree = getParseTree(source, name='receiveNetstring')
        i = Interp(parseTree, None)
        i.names['cb'] = cb
        i.receive('ab')
        self.assertEqual(_calls, ['b'])


class TestUtils(TestCase):
    def test_successExits(self):
        n1 = Node(matcher=1)
        n2 = Node(matcher=2)
        n3 = Node(matcher=3)
        n1.success.append(setRule(node=n2))
        n1.failure.append(setRule(node=n3))

        exits = list(successExits(n1))
        self.assertNotIn(n1, exits)
        self.assertIn(n2, exits)
        self.assertIn(n3, exits)
