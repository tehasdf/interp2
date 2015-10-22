from ometa.interp import TrampolinedGrammarInterpreter, _feed_me, decomposeGrammar
from ometa.grammar import OMeta
from parsley import makeGrammar


grammar = OMeta("""
a = anything{1}:a 'b' -> receiver.receive(a)
""").parseGrammar('Grammar')

# class _Receiver(object):
#     def receive(self, x):
#         print 'received', repr(x)
# bindings = {'receiver': _Receiver()}
# currentRule = 'a'
# interp = TrampolinedGrammarInterpreter(grammar, rule=currentRule,
#     callback=None, globals=bindings)

# print interp.receive('1')

from p2 import Interp, ParseError



from twisted.trial.unittest import TestCase

class TestInterp(TestCase):

    def test_parses(self):
        inputs = [
            'ab', 'ac', 'adz', 'axy', 'axz', 'ady',
        'axf']
        for i in inputs:
            calls = []
            def _cb():
                calls.append(True)
            interp = Interp(grammar, _cb)
            interp.receive(i)
            self.assertEqual(len(calls), 1)

    def test_errors(self):
        inputs = ['ay', 'adn', 'axm']
        for i in inputs:
            calls = []
            def _cb():
                calls.append(True)

            with self.assertRaises(ParseError):
                interp = Interp(grammar, _cb)
                interp.receive(i)
            self.assertEqual(len(calls), 0)

    def test_notDoneParsing(self):
        inputs = ['a', 'ad', 'ax']
        for i in inputs:
            calls = []
            def _cb():
                calls.append(True)

            interp = Interp(grammar, _cb)
            interp.receive(i)
            self.assertEqual(len(calls), 0)


    def test_parsingDone(self):
        inputs = ['abf', 'adzy', 'axzq']
        for i in inputs:
            calls = []
            def _cb():
                calls.append(True)

            interp = Interp(grammar, _cb)
            interp.receive(i)
            self.assertEqual(len(calls), 1)

    def test_incremental(self):
        calls = []
        def _cb():
            calls.append(True)

        interp = Interp(grammar, _cb)
        interp.receive('a')
        self.assertEqual(len(calls), 0)
        interp.receive('x')
        self.assertEqual(len(calls), 0)
        interp.receive('z')
        self.assertEqual(len(calls), 1)