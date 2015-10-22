from ometa.interp import decomposeGrammar
from ometa.grammar import OMeta
from parsley import makeGrammar

from matchers import anything, exact, Node, FailureNode
from interp import Interp, ParseError
from util import TestBase


def _multipleAlternativesOr(alternatives):
    matchers = [compileRule(rule) for rule in alternatives]
    for current_node, next_node in zip(matchers, matchers[1:]):
        count = 0
        while True:
            if current_node.failure is None:
                current_node.failure = FailureNode(node=next_node, backtrack=count)
            else:
                raise ValueError('???')
            count += 1
            if current_node.success is None:
                break
            current_node = current_node.success
    return matchers[0]

def orHandler(term):
    alt_tag = term.args[0]
    assert alt_tag.tag.name == '.tuple.'
    alternatives = alt_tag.args

    if len(alternatives) == 1:
        return compileRule(alternatives[0])
    else:
        return _multipleAlternativesOr(alternatives)

def _simpleRepeatHandler(num, rule, *args):
    if rule.data == 'anything':
        return Node(matcher=anything(length=int(num)))
    else:
        raise NotImplementedError()


def repeatHandler(repeat):
    min_repeat, max_repeat, term = repeat.args
    if min_repeat == max_repeat and term.tag.name == 'Apply':
        return _simpleRepeatHandler(min_repeat, *term.args)
    else:
        raise NotImplementedError()

def andHandler(term):
    elements = term.args[0].args
    matchers = [compileRule(rule) for rule in elements]
    for current_node, next_node in zip(matchers, matchers[1:]):
        while current_node.success is not None:
            current_node = current_node.success
        current_node.success = next_node
    return matchers[0]

def exactlyHandler(term):
    target_tag = term.args[0]
    target = target_tag.data
    return Node(matcher=exact(target))

handlers = {
    'Or': orHandler,
    'Repeat': repeatHandler,
    'And': andHandler,
    'Exactly': exactlyHandler
}

def compileRule(rule):
    handler = handlers[rule.tag.name]
    parsed = handler(rule)
    return parsed

def getRule(source, name=None):
    o = OMeta(source).parseGrammar('grammar')
    if name is None:
        return decomposeGrammar(o).values()[0]
    else:
        return decomposeGrammar(o)[name]

class TestCompiler(TestBase):
    def test_and(self):
        source = """
        a = 'b' 'c' 'de'
        """
        parseTree = compileRule(getRule(source))
        self.assertMatch(parseTree, 'bcde')
        self.assertNoMatch(parseTree, 'bcd')

    def test_doubleand(self):
        source = """
        a = ('b' 'c') ('d' 'e')
        """
        parseTree = compileRule(getRule(source))
        self.assertMatch(parseTree, 'bcde')


    def test_andor(self):
        source = """
        a = anything{1} ('b' | 'c')
        """
        parseTree = compileRule(getRule(source))
        self.assertMatch(parseTree, 'ab')
        self.assertMatch(parseTree, 'ac')
        self.assertNoMatch(parseTree, 'ad')

    def test_orAndOr(self):
        source = """
        a = ('b' | 'c') ('d' | 'e')
        """
        parseTree = compileRule(getRule(source))
        for i in ['bd', 'cd', 'be', 'bd']:
            self.assertMatch(parseTree, i)
        self.assertNoMatch(parseTree, 'bc')

    def test_needsBacktracking(self):
        source = """
        a = ('a' 'b') | ('a' 'c') | 'z'
        """
        parseTree = compileRule(getRule(source))
        self.assertMatch(parseTree, 'ab')
        self.assertNoMatch(parseTree, 'aa')
        self.assertMatch(parseTree, 'ac')
        self.assertMatch(parseTree, 'z')

    def test_moreBacktracking(self):
        source = """
        a = ('a' 'b' 'c' 'd' 'e' 'f') | ('a' 'b' 'c' 'd' 'e' 'z')
        """
        parseTree = compileRule(getRule(source))
        self.assertMatch(parseTree, 'abcdez')
