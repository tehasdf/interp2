from interp import Interp, ParseError
from matchers import exact, anything, Node, FailureNode
from util import TestBase

class TestInterp(TestBase):
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
    xf_or = Node(
        matcher=exact('x'),
        success=Node(matcher=exact('f'))
    )

    dy_or = Node(
        matcher=exact('d'),
        success=Node(matcher=exact('y')),
        failure=FailureNode(node=xf_or)
    )

    z_or = Node(
        matcher=exact('z'),
        failure=FailureNode(node=dy_or, backtrack=1)
    )
    x_or = Node(
        matcher=exact('x'),
        success=Node(
            matcher=exact('y'),
            failure=FailureNode(node=z_or)
        ),
        failure=FailureNode(node=dy_or)
    )

    d_or = Node(
        matcher=exact('d'),
        success=Node(
            matcher=exact('z'),
            failure=FailureNode(node=x_or, backtrack=1)
        ),
        failure=FailureNode(node=x_or)
    )

    c_or = Node(
        matcher=exact('c'),
        failure=FailureNode(node=d_or)
    )

    parseTree = Node(
        matcher=anything(length=1),
        success=Node(
            matcher=exact('b'),
            failure=FailureNode(node=c_or)
        )

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

    def test_orThenAnd(self):
        """
        a = ('b' | 'c') 'a'
        """
        aNode = Node(matcher=exact('a'))
        cNode = Node(matcher=exact('c'), success=aNode)
        parseTree = Node(
            matcher=exact('b'),
            success=aNode,
            failure=FailureNode(node=cNode)
        )
        self.assertMatch(parseTree, 'ba')
        self.assertMatch(parseTree, 'ca')
        self.assertNoMatch(parseTree, 'bca')

