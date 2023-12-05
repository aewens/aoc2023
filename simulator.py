#!/usr/bin/env python3

from ewenix.repl import REPL
from ewenix.util import mint

from time import perf_counter
from random import randint

def main():
    repl = REPL()

    done, result = repl.execute("help")
    assert done is False, "Invalid help result 1"
    assert len(result.split("\n")) == 10, "Invalid help result 2"

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

    repl.sched.clear()
    print(f"Echo Benchmark: {perf_counter()-timer3:.05f}s")

    timer4 = perf_counter()

    assert repl.mem.mem[0] == 0, repl.mem.mem[0]

    error, result = repl.mem.alloc(1024)
    assert error is False, result
    assert isinstance(result, int), result
    pointer = result

    error, result = repl.mem.alloc(1)
    assert error is True, result
    assert isinstance(result, str), result

    error, result = repl.mem.read(pointer, 4)
    assert error is False, result
    assert result == [0,0,0,0], result

    error, result = repl.mem.free(pointer)
    assert error is False, result
    assert result is None, result

    error, result = repl.mem.alloc(4)
    assert error is False, result
    assert isinstance(result, int), result
    pointer = result

    error, result = repl.mem.write(pointer, [1,2,3,4])
    assert error is False, result
    assert isinstance(result, int), result

    error, result = repl.mem.read(pointer, 4)
    assert error is False, result
    assert result == [1,2,3,4], result

    repl.mem.clear()
    print(f"Memory Benchmark: {perf_counter()-timer4:.05f}s")

    done, result = repl.execute("alloc 4")
    assert done is False, "Invalid alloc result 1"
    try:
        assert isinstance(int(result), int), result

    except Exception as e:
        assert False, (result, e)

    pointer = result
    done, result = repl.execute(f"write {pointer} 1 2 3 4")
    assert done is False, "Invalid write result 1"
    assert isinstance(result, int), result

    done, result = repl.execute(f"read {pointer} 4")
    assert done is False, "Invalid read result 1"
    assert result == [1,2,3,4], result

    repl.mem.clear()

    raw = {"key": "value", "numbers": [1,2,3]}
    res = "d3:key5:value7:numbersli1ei2ei3eee"
    encoded = repl.encode(raw)
    assert encoded == res, encoded

    junk, decoded = repl.decode(encoded)
    assert junk == "", junk
    assert decoded == raw, decoded

    timer5 = perf_counter()

    subject = '@{"key": "value", "numbers": [1,2,3]}'
    done, result = repl.execute(f"bwrite -1 {subject}")
    assert done is False, "Invalid bwrite result 1"
    assert isinstance(result, int), result

    pointer = result

    done, result = repl.execute(f"bread {pointer} {len(res)}")
    assert done is False, "Invalid bread result 1"
    assert result == raw, result

    print(f"Bencode Benchmark: {perf_counter()-timer4:.05f}s")

if __name__ == "__main__":
    main()
