interp2
=======

This is an experiment to see if it's possible to create a better performance
execution model for parsley, the python parser generator library.

This takes the AST generated by parsley/OMeta, and transforms it into a
DFSM, which then parses the input data.

The DFSM is represented by Node instances (`interp2.matchers.Node`),
where each Node has a `matcher`, and `success` and `failure` callbacks.
If the `matcher` inside the Node matches the input data, success callbacks are
executed; otherwise, failure callbacks. Any number of callbacks is allowed,
but typically one of them will be a "go to the next state (next node)"
operation (`interp2.matchers.setRule`)


Hacking
-------

To run the tests, simply run `py.test interp2`


TODO
----

* refactor the thing
* needs testing at the compiler level, with examining resulting nodes
* rewrite the compiler as a compiler + optimizer
* add more support for parsley syntax (the uncodumented "@" etc)