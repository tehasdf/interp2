from parsley import makeGrammar


g = makeGrammar("""
            a = digit*
    """, {})

print g('122').a()