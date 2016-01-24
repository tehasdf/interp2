
class AndHandler(object):
    def __init__(self, term, *args):
        self.term = term
        import pudb; pu.db

handlers = {
    'And': AndHandler
}

def r(rule):
    if rule.tag.name == 'Or' and len(rule.args) == 1:
        rule = rule.args[0].args[0]
    handler = handlers[rule.tag.name]
    c = handler(*rule.args)
    return rule


class anything(object):
    def __init__(self, name, length):
        self._name = name
        self._length = length

        self.min = length
        self.prefix_min = length

    def match(self, data):
        return data[:self._length], data[self._length:]


class exact(object):
    def __init__(self, name, target):
        self._name = name
        self._target = target
        self.min = self.prefix_min = len(target)

    def match(self, data):
        if data.startswith(self._target):
            return data[:self.min], data[self.min:]
        else:
            raise ParseError()

class or_(object):
    def __init__(self, name, alternatives):
        self._name = name
        self.alternatives = alternatives



class R(object):
    def __init__(self):
        self._ix = 0
        self.rules = [
            anything('a', length=1),
            exact(None, target='b'),
            or_(None, [
                exact(None, target='b'),
                exact(None, target='c')
            ])
        ]

    def getMatcher(self):
        try:
            return self.rules[self._ix]
        except IndexError:
            return None

    def next(self):
        self._ix += 1


class ParseError(Exception):
    pass


class Interp(object):
    def __init__(self, grammar, rule):
        self._data = ''
        self.rules = R()
        self.matcher = self.rules.getMatcher()
        self.names = {}

    def receive(self, data):
        self._data += data
        self._tryParse()

    def _tryParse(self):
        while self._data:
            if len(self._data) >= self.matcher.min:
                try:
                    matched, self._data = self.matcher.match(self._data)
                except ParseError:
                    self.matcherError()
                else:
                    self.names[self.matcher._name] = matched
                    self.nextMatcher()
            elif len(self._data) >= self.matcher.prefix_min:
                if not self.matcher.test_prefix(self._data):
                    self.matcherError()
            else:
                break

    def nextMatcher(self):
        self.rules.next()
        self.matcher = self.rules.getMatcher()
        if self.matcher is None:
            print 'done', self.names

    def matcherError(self):
        print 'matcher error'
        raise ParseError()