

class anything(object):
    def __init__(self, length):
        self.need = length
        self._received = ''

    def receive(self, data):
        return self.need

    def __repr__(self):
        return '<anything %d>' % (self.need, )

class exact(object):
    def __init__(self, target):
        self._target = target
        self.need = len(target)

    def receive(self, data):
        if data.startswith(self._target):
            return self.need
        else:
            raise ParseError('exact expected %r, got %r' % (self._target, data))

    def __repr__(self):
        return '<exact %s>' % (self._target, )

parseTree = (
    anything(length=1),
    (
        exact(target='b'),
        None,
        (
            (
                exact(target='c'),
                None,
                None
            ),
        0)
    ),
    None
)


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

class ParseError(Exception):
    pass

class Interp(object):
    def __init__(self, grammar, callback):
        self.next(parseTree)
        self._ix = 0
        self.stack = []
        self._data = ''
        self.callback = callback

    def next(self, tree):
        self.current, self.onSuccess, self.onFailure = tree

    def receive(self, data):
        self._data += data
        self._tryParse()

    def _tryParse(self):
        while True:
            newDataLen = len(self._data) - self._ix
            if newDataLen < self.current.need:
                break

            try:
                move = self.current.receive(self._data[self._ix:])
            except ParseError:
                if self.onFailure is not None:
                    nexthandler, backtrack = self.onFailure
                    for _ in range(backtrack):
                        self._ix -= self.stack.pop()
                    self.next(nexthandler)
                    continue
                else:
                    raise

            if move is None:
                break
            self._ix += move
            self.stack.append(move)

            if self.onSuccess is None:
                self.callback()
                return

            self.next(self.onSuccess)

