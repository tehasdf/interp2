from ometa.interp import decomposeGrammar
from twisted.trial.unittest import TestCase
from ometa.grammar import OMeta
from parsley import makeGrammar


from interp2.matchers import anything, exact, Node, setRule, backtrack, setName, digit, noop, many
from interp2.interp import Interp, ParseError
from interp2.util import TestBase


def _transitionWhere(cbs):
    for cb in cbs:
        if isinstance(cb, setRule):
            return cb.node

def getSuccessNode(node):
    return _transitionWhere(node.success)

def getSuccessLeaf(node):
    while True:
        next_node = getSuccessNode(node)
        if next_node is None:
            break
        node = next_node
    return node

def successExits(node):
    rv = []
    while True:
        next_fail = _transitionWhere(node.failure)
        if next_fail is not None:
            for nested_node in successExits(next_fail):
                rv.append(nested_node)
        next_success = _transitionWhere(node.success)
        if next_success is None:
            rv.append(node)
            break
        else:
            node = next_success
    return rv


class Compiler(object):
    def __init__(self, source):
        self.source = source
        self.grammar = OMeta(source).parseGrammar('grammar')
        self.rules = decomposeGrammar(self.grammar)

    def getRule(self, name=None):
        if name is None:
            return self.rules.values()[0]
        else:
            return self.rules[name]

    def compileRule(self, rule):
        handler = getattr(self, 'handle_%s' % (rule.tag.name, ))
        parsed = handler(rule)
        return parsed

    def _multipleAlternativesOr(self, alternatives):
        matchers = [self.compileRule(rule) for rule in alternatives]
        for current_node, next_node in zip(matchers, matchers[1:]):
            count = 0
            while current_node is not None:
                current_node.failure.append(setRule(node=next_node))
                if count > 0:
                    current_node.failure.append(backtrack(count=count))
                count += 1
                if not current_node.success:
                    break
                current_node = getSuccessNode(current_node)
        return matchers[0]

    def handle_Or(self, term):
        alt_tag = term.args[0]
        assert alt_tag.tag.name == '.tuple.'
        alternatives = alt_tag.args

        if len(alternatives) == 1:
            return self.compileRule(alternatives[0])
        else:
            return self._multipleAlternativesOr(alternatives)

    def _simpleRepeatHandler(self, num, rule, *args):
        if rule.data == 'anything':
            return Node(matcher=(anything, {'length': num}))
        elif rule.data == 'digit':
            return Node(matcher=(digit, {'length': num}))
        else:
            try:
                return self.compileRule(self.getRule(rule.data))
            except KeyError:
                raise NotImplementedError('_simpleRepeatHandler: unknown rule: %s' % (rule.data, ))


    def handle_Repeat(self, repeat):
        min_repeat, max_repeat, term = repeat.args
        if min_repeat == max_repeat and term.tag.name == 'Apply':
            return self._simpleRepeatHandler(min_repeat, *term.args)
        else:
            raise NotImplementedError()

    def handle_And(self, term):
        elements = term.args[0].args
        matchers = [self.compileRule(rule) for rule in elements]
        seen = []
        for current_node, next_node in zip(matchers, matchers[1:]):
            for x in successExits(current_node):
                # XXX this is dirty - should successExits actually return the same
                # node more than once?
                if x in seen:
                    continue
                seen.append(x)
                if issubclass(next_node.matcher[0], noop):
                    x.success.extend(next_node.success)
                else:
                    x.success.append(setRule(node=next_node))

        return matchers[0]

    def handle_Exactly(self, term):
        target_tag = term.args[0]
        target = target_tag.data
        return Node(matcher=(exact, {'target': target}))

    def handle_Bind(self, term):
        nameTerm, rule = term.args
        rule = self.compileRule(rule)
        for target_rule in successExits(rule):
            target_rule.success.append(setName(name=nameTerm.data))
        return rule

    def handle_Apply(self, term):
        return self._simpleRepeatHandler(1, *term.args)

    def handle_Predicate(self, term):
        val = term.args[0]
        if val.tag.name != 'Action':
            raise NotImplementedError()

        code = val.args[0].data
        def pred(interp, rv):
            if eval(code, {}, interp.names):
                return rv
            else:
                raise ParseError('failed predicate')
        return Node(matcher=(noop, {}), success=[pred])


    def handle_Many(self, term):
        nested = term.args[0]
        rule = self.compileRule(nested)
        return Node(matcher=(many, {'rule': rule}))

    def handle_ConsumedBy(self, term):
        nested = self.compileRule(term.args[0])

        class consumer(object):
            def __init__(self):
                self.data = []

            def push(self):
                def _doPush(interp, rv):
                    if isinstance(rv, list):
                        self.data.extend(rv)
                    else:
                        self.data.append(rv)
                    return rv
                return _doPush

            def backtrack(self, count):
                def _doBacktrack(interp, rv):
                    self.data = self.data[:-count]
                    return rv
                return _doBacktrack

            def finish(self):
                def _doFinish(interp, rv):
                    return ''.join(self.data)
                return _doFinish
            def clear(self):
                def _f(interp, rv):
                    self.data = []
                    return rv
                return _f

        _c = consumer()
        seen = []

        def _f(node):
            if node in seen:
                return
            seen.append(node)
            count = 0
            while True:
                fail_node = _transitionWhere(node.failure)
                if fail_node is not None:
                    _f(fail_node)
                node.success.append(_c.push())
                if count > 0:
                    node.failure.append(_c.backtrack(count))
                count += 1
                next_node = getSuccessNode(node)
                if next_node is None:
                    node.success.append(_c.finish())
                    break
                else:
                    node = next_node

        _f(nested)
        nested.success.insert(0, _c.clear())
        nested.failure.insert(0, _c.clear())
        return nested

    def handle_Action(self, term):
        code = term.args[0].data
        compiled = compile(code, '<string>', 'eval')
        def act(interp, rv):
            return eval(compiled, {}, interp.names)
        return Node(matcher=(noop, {}), success=[act])
