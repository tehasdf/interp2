from interp import Interp, ParseError
from ometa.interp import decomposeGrammar
from ometa.grammar import OMeta
from twisted.trial.unittest import TestCase

def getRule(source, name):
    o = OMeta(source).parseGrammar('grammar')
    return decomposeGrammar(o)[name]


def _numMatches(parseTree, data, name='a'):


    _calls = []
    def _cb():
        _calls.append(True)

    i = Interp(parseTree, _cb)
    try:
        i.receive(data)
    except ParseError as e:
        return 0
    return len(_calls)

class TestBase(TestCase):
    def assertMatch(self, *args):
        self.assertEqual(_numMatches(*args), 1)

    def assertNoMatch(self, *args):
        self.assertEqual(_numMatches(*args), 0)
