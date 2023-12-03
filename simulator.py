#!/usr/bin/env python3

from ewenix.repl import REPL
from time import perf_counter

def main():
    repl = REPL()

    done, result = repl.execute("help")
    assert done is False, "Invalid help result 1"
    assert len(result.split("\n")) == 3, "Invalid help result 2"

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

    print(f"Quit Benchmark: {perf_counter()-timer1:.05f}s")

if __name__ == "__main__":
    main()
