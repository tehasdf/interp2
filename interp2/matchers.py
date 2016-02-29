from interp import ParseError, Interp
from characteristic import attributes, Attribute

class anything(object):
    def __init__(self, interp, length):
        try:
            length = int(length)
        except ValueError:
            length = interp.names[length.data]
        self.need = length
        self._received = ''

    def receive(self, data, previous):
        return self.need, data[:self.need]

    def __repr__(self):
        return '<anything %d>' % (self.need, )

class exact(object):
    def __init__(self, interp, target):
        self._target = target
        self.need = 1

    def receive(self, data, previous):
        if len(data) < len(self._target):
            if self._target.startswith(data):
                return None, None
            else:
                raise ParseError('%r is not a prefix of %r' % (data, self._target))
        if data.startswith(self._target):
            return len(self._target), self._target
        else:
            raise ParseError('exact expected %r, got %r' % (self._target, data))

    def __repr__(self):
        return '<exact %s>' % (self._target, )


class digit(object):
    # XXX needs _received
    def __init__(self, interp, length):
        self.need = length

    def receive(self, data, previous):
        received = data[:self.need]
        if received.isdigit():
            return self.need, received
        else:
            raise ParseError('not digit')


class many(object):
    def __init__(self, interp, rule):
        rule.success = [self._store, setRule(node=rule)]

        self.interp = Interp(rule)
        self.gathered = []

    @property
    def need(self):
        return self.interp.current.need

    def receive(self, data, previous):
        try:
            self.interp.receive(data)
        except ParseError:
            return self.interp._ix, self.gathered
        return None, None

    def _store(self, interp, rv):
        self.gathered.append(rv)


class noop(object):
    # XXX get rid of that, compiler should instead append the cb to the previous node
    need = 0
    def __init__(self, interp):
        pass

    def receive(self, data, previous):
        return 0, previous

@attributes(['matcher',
    Attribute('success', default_factory=list),
    Attribute('failure', default_factory=list)])
class Node(object):
    pass


@attributes(['node'])
class setRule(object):
    def __call__(self, interp, rv):
        interp.next(self.node)
        return rv

@attributes(['count'])
class backtrack(object):
    def __call__(self, interp, rv):
        for _ in range(self.count):
            interp._ix -= interp.stack.pop()
        return rv

@attributes(['name'])
class setName(object):
    def __call__(self, interp, rv):
        interp.names[self.name] = rv
        return rv
