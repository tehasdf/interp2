from interp import ParseError

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
