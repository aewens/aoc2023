#!/usr/bin/env python3

from ewenix.repl import REPL
from ewenix.util import mint

from time import perf_counter
from random import randint

def main():
    repl = REPL()

    done, result = repl.execute("help")
    assert done is False, "Invalid help result 1"
    assert len(result.split("\n")) == 4, "Invalid help result 2"

    done, result = repl.execute("print hello world")
    assert done is False, "Invalid print result 1"
    assert result == "hello world", "Invalid print result 2"

    done, result = repl.execute("quit")
    assert done is True, "Invalid quit result"

    timer0 = perf_counter()
    for i in range(1000):
        done, result = repl.execute("help")

    print(f"Help Benchmark: {perf_counter()-timer0:.05f}s")

    timer1 = perf_counter()
    for i in range(1000):
        done, result = repl.execute("print hello world")

    print(f"Print Benchmark: {perf_counter()-timer1:.05f}s")

    timer2 = perf_counter()
    for i in range(1000):
        done, result = repl.execute("quit")

    print(f"Quit Benchmark: {perf_counter()-timer2:.05f}s")

    done, result = repl.execute("echo 3 hello world")
    assert done is False, "Invalid echo result 1"
    assert result.startswith("Queued"), "Invalid echo result 2"

    timer3 = perf_counter()
    repl.sched.clear()
    for i in range(1000):
        j = randint(1, 1000)
        repl.execute(f"echo {j} {j}")

    prev = None
    while len(repl.sched.queue) > 0:
        done, result = repl.process()
        value = mint(result, 0)
        assert done is False, "Invalid echo result 3"
        if prev is not None:
            assert value >= prev, f"{prev} > {value}"

        prev = value

    print(f"Echo Benchmark: {perf_counter()-timer3:.05f}s")

if __name__ == "__main__":
    main()
