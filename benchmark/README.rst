Benchmarking
=============

For now this only contains a simple "netstrings" benchmark with just a few
test cases.
The interesting case is long netstrings, because in that setup, parsley is
terribly slow.

To run the benchmarks, simply do `python -m benchmark.runbenchmark`


Example output:

    parsley short and simple took 0:00:00.032414
    parsley many short messages took 0:00:00.478769
    parsley long messages took 0:00:04.700344
    parsley many long messages took 0:00:20.034139
    interp2 short and simple took 0:00:00.038897
    interp2 many short messages took 0:00:00.383198
    interp2 long messages took 0:00:00.040608
    interp2 many long messages took 0:00:00.064451
