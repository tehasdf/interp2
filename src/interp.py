
class ParseError(Exception):
    pass

class Interp(object):
    def __init__(self, parseTree, callback):
        self.next(parseTree)
        self._ix = 0
        self.stack = []
        self._data = ''
        self.callback = callback

    def next(self, node):
        self.current = node.matcher
        self.onSuccess = node.success
        self.onFailure = node.failure

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
                if self.onFailure:
                    for errback in self.onFailure:
                        errback(self)
                    continue
                else:
                    raise

            if move is None:
                break

            self._ix += move
            self.stack.append(move)

            if not self.onSuccess:
                self.callback()
                return

            for callback in self.onSuccess:
                callback(self)

