
class ParseError(Exception):
    pass

class Interp(object):
    def __init__(self, parseTree, callback):
        self.next(parseTree)
        self._ix = 0
        self.stack = []
        self._data = ''
        self.callback = callback

    def next(self, tree):
        self.current = tree.matcher
        self.onSuccess = tree.success
        self.onFailure = tree.failure

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
                    nexthandler = self.onFailure.node
                    backtrack = self.onFailure.backtrack
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
