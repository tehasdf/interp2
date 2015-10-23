from interp import ParseError
from characteristic import attributes, Attribute

class anything(object):
    def __init__(self, length):
        self.need = length
        self._received = ''

    def receive(self, data):
        return self.need, data[:self.need]

    def __repr__(self):
        return '<anything %d>' % (self.need, )

class exact(object):
    def __init__(self, target):
        self._target = target
        self.need = len(target)

    def receive(self, data):
        if data.startswith(self._target):
            return self.need, self._target
        else:
            raise ParseError('exact expected %r, got %r' % (self._target, data))

    def __repr__(self):
        return '<exact %s>' % (self._target, )


@attributes(['matcher',
    Attribute('success', default_factory=list),
    Attribute('failure', default_factory=list)])
class Node(object):
    pass


@attributes(['node'])
class setRule(object):
    def __call__(self, interp, rv):
        interp.next(self.node)

@attributes(['count'])
class backtrack(object):
    def __call__(self, interp, rv):
        for _ in range(self.count):
            interp._ix -= interp.stack.pop()


@attributes(['name'])
class setName(object):
    def __call__(self, interp, rv):
        interp.names[self.name] = rv