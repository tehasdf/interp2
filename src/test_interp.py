from interp import Interp, ParseError
from matchers import exact, anything
from twisted.trial.unittest import TestCase


class TestInterp(TestCase):
    """
    a = anything{1} (
        'b'
        | ('c' | ('d' 'z'))
        | 'x' ('y' | 'z')
        | ('d' 'y')
        | ('x' 'f')
        )

    # ab
    # ac
    # adz
    # axy
    # axz
    # ady
    # axf
    """
    xf_or = (
        exact('x'),
        (exact('f'), None, None),
        None
    )

    dy_or = (
        exact('d'),
        (exact('y'), None, None),
        (xf_or, 0)
    )

    z_or = (exact('z'), None, (dy_or, 1))
    x_or = (
        exact('x'),
        (
            exact('y'),
            None,
            (z_or, 0)
        ),
        (dy_or, 0)
    )

    d_or = (
        exact('d'),
        (
            exact('z'), None, (x_or, 1)
        ),
        (x_or, 0)
    )

    c_or = (
        exact('c'),
        None,
        (d_or, 0)
    )

    parseTree = (
        anything(length=1),

        (
            exact('b'),
            None,
            (c_or, 0)
        ),
        None

    )

    def test_parses(self):
        inputs = [
            'ab', 'ac', 'adz', 'axy', 'axz', 'ady',
        'axf']
        for i in inputs:
            calls = []
            def _cb():
                calls.append(True)
            interp = Interp(self.parseTree, _cb)
            interp.receive(i)
            self.assertEqual(len(calls), 1)

    def test_errors(self):
        inputs = ['ay', 'adn', 'axm']
        for i in inputs:
            calls = []
            def _cb():
                calls.append(True)

            with self.assertRaises(ParseError):
                interp = Interp(self.parseTree, _cb)
                interp.receive(i)
            self.assertEqual(len(calls), 0)

    def test_notDoneParsing(self):
        inputs = ['a', 'ad', 'ax']
        for i in inputs:
            calls = []
            def _cb():
                calls.append(True)

            interp = Interp(self.parseTree, _cb)
            interp.receive(i)
            self.assertEqual(len(calls), 0)


    def test_parsingDone(self):
        inputs = ['abf', 'adzy', 'axzq']
        for i in inputs:
            calls = []
            def _cb():
                calls.append(True)

            interp = Interp(self.parseTree, _cb)
            interp.receive(i)
            self.assertEqual(len(calls), 1)

    def test_incremental(self):
        calls = []
        def _cb():
            calls.append(True)

        interp = Interp(self.parseTree, _cb)
        interp.receive('a')
        self.assertEqual(len(calls), 0)
        interp.receive('x')
        self.assertEqual(len(calls), 0)
        interp.receive('z')
        self.assertEqual(len(calls), 1)
