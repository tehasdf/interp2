
class ParseError(Exception):
    pass

class Interp(object):
    def __init__(self, parseTree, callback=None):
        self.next(parseTree)
        self._ix = 0
        self.stack = []
        self.names = {}
        self._data = ''
        self.callback = callback
        self.ended = False
        self.rv = None

    def next(self, node):
        self.current = node.matcher
        self.onSuccess = node.success
        self.onFailure = node.failure

    def receive(self, data):
        self._data += data
        if not self.ended:
            self._tryParse()

    def _tryParse(self):
        while True:
            newDataLen = len(self._data) - self._ix
            if newDataLen < self.current.need:
                break
            try:
                move, self.rv = self.current.receive(self._data[self._ix:], self.rv)
            except ParseError as e:
                if self.onFailure:
                    for errback in self.onFailure:
                        self.rv = errback(self, self.rv)
                    continue
                else:
                    raise

            if move is None:
                break

            self._ix += move
            self.stack.append(move)

            self.current = None

            for callback in self.onSuccess:
                self.rv = callback(self, self.rv)


            if self.current is None:
                if self.callback is not None:
                    self.callback()
                self.ended = True
                return
