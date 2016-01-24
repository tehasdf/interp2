from ometa.interp import decomposeGrammar
from twisted.trial.unittest import TestCase
from ometa.grammar import OMeta
from parsley import makeGrammar

from interp2.matchers import anything, exact, Node, setRule, backtrack, setName, digit, noop, many
from interp2.interp import Interp, ParseError
from interp2.util import TestBase


def _transitionWhere(cbs):
    for cb in cbs:
        if isinstance(cb, setRule):
            return cb.node

def getSuccessNode(node):
    return _transitionWhere(node.success)

def getSuccessLeaf(node):
    while True:
        next_node = getSuccessNode(node)
        if next_node is None:
            break
        node = next_node
    return node

def successExits(node):
    rv = []
    while True:
        next_fail = _transitionWhere(node.failure)
        if next_fail is not None:
            for nested_node in successExits(next_fail):
                rv.append(nested_node)
        next_success = _transitionWhere(node.success)
        if next_success is None:
            rv.append(node)
            break
        else:
            node = next_success
    return rv


class Compiler(object):
    def __init__(self, source):
        self.source = source
        self.grammar = OMeta(source).parseGrammar('grammar')
        self.rules = decomposeGrammar(self.grammar)

    def getRule(self, name=None):
        if name is None:
            return self.rules.values()[0]
        else:
            return self.rules[name]

    def compileRule(self, rule):
        handler = getattr(self, 'handle_%s' % (rule.tag.name, ))
        parsed = handler(rule)
        return parsed

    def _multipleAlternativesOr(self, alternatives):
        matchers = [self.compileRule(rule) for rule in alternatives]
        for current_node, next_node in zip(matchers, matchers[1:]):
            count = 0
            while current_node is not None:
                current_node.failure.append(setRule(node=next_node))
                if count > 0:
                    current_node.failure.append(backtrack(count=count))
                count += 1
                if not current_node.success:
                    break
                current_node = getSuccessNode(current_node)
        return matchers[0]

    def handle_Or(self, term):
        alt_tag = term.args[0]
        assert alt_tag.tag.name == '.tuple.'
        alternatives = alt_tag.args

        if len(alternatives) == 1:
            return self.compileRule(alternatives[0])
        else:
            return self._multipleAlternativesOr(alternatives)

    def _simpleRepeatHandler(self, num, rule, *args):
        if rule.data == 'anything':
            return Node(matcher=(anything, {'length': num}))
        elif rule.data == 'digit':
            return Node(matcher=(digit, {'length': num}))
        else:
            try:
                return self.compileRule(self.getRule(rule.data))
            except KeyError:
                raise NotImplementedError('_simpleRepeatHandler: unknown rule: %s' % (rule.data, ))


    def handle_Repeat(self, repeat):
        min_repeat, max_repeat, term = repeat.args
        if min_repeat == max_repeat and term.tag.name == 'Apply':
            return self._simpleRepeatHandler(min_repeat, *term.args)
        else:
            raise NotImplementedError()

    def handle_And(self, term):
        elements = term.args[0].args
        matchers = [self.compileRule(rule) for rule in elements]
        for current_node, next_node in zip(matchers, matchers[1:]):
            # if issubclass(next_node.matcher[0], noop):
            #     continue
            # while True:
            #         success_node = getSuccessNode(current_node)
            #         if success_node is None:
            #             break
            #         current_node = success_node
            for x in successExits(current_node):
                if issubclass(next_node.matcher[0], noop):
                    x.success.extend(next_node.success)
                else:
                    x.success.append(setRule(node=next_node))

        return matchers[0]

    def handle_Exactly(self, term):
        target_tag = term.args[0]
        target = target_tag.data
        return Node(matcher=(exact, {'target': target}))

    def handle_Bind(self, term):
        nameTerm, rule = term.args
        rule = self.compileRule(rule)
        for target_rule in successExits(rule):
            target_rule.success.append(setName(name=nameTerm.data))
        return rule

    def handle_Apply(self, term):
        return self._simpleRepeatHandler(1, *term.args)

    def handle_Predicate(self, term):
        val = term.args[0]
        if val.tag.name != 'Action':
            raise NotImplementedError()

        code = val.args[0].data
        def pred(interp, rv):
            if eval(code, {}, interp.names):
                return rv
            else:
                raise ParseError('failed predicate')
        return Node(matcher=(noop, {}), success=[pred])


    def handle_Many(self, term):
        nested = term.args[0]
        rule = self.compileRule(nested)
        return Node(matcher=(many, {'rule': rule}))

    def handle_ConsumedBy(self, term):
        nested = self.compileRule(term.args[0])

        class consumer(object):
            def __init__(self):
                self.data = []

            def push(self):
                def _doPush(interp, rv):
                    if isinstance(rv, list):
                        self.data.extend(rv)
                    else:
                        self.data.append(rv)
                    return rv
                return _doPush

            def backtrack(self, count):
                def _doBacktrack(interp, rv):
                    self.data = self.data[:-count]
                    return rv
                return _doBacktrack

            def finish(self):
                def _doFinish(interp, rv):
                    return ''.join(self.data)
                return _doFinish
            def clear(self):
                def _f(interp, rv):
                    self.data = []
                    return rv
                return _f
        _c = consumer()
        seen = []
        def _f(node):
            if node in seen:
                return
            seen.append(node)
            count = 0
            while True:
                fail_node = _transitionWhere(node.failure)
                if fail_node is not None:
                    _f(fail_node)
                node.success.append(_c.push())
                if count > 0:
                    node.failure.append(_c.backtrack(count))
                count += 1
                next_node = getSuccessNode(node)
                if next_node is None:
                    node.success.append(_c.finish())
                    break
                else:
                    node = next_node

        _f(nested)
        nested.success.insert(0, _c.clear())
        return nested

    def handle_Action(self, term):
        code = term.args[0].data
        def act(interp, rv):
            return eval(code, {}, interp.names)
        return Node(matcher=(noop, {}), success=[act])


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
