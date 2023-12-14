from heapq import heappush, heappop, heapify
from struct import pack, unpack
from time import time

MINIMUM = float("-inf")

def leftpad(xs, size, pad="0"):
    count = len(xs)
    if count >= size:
        return xs

    padding = [pad] * (size-count)
    return padding + xs

class MinHeap:
    def __init__(self):
        self.heap = list()

    def parent(self, index):
        return (i-1)/2

    def push(self, key):
        heappush(self.heap, key)

    def dec(self, index, new_value):
        """
        Decrease value of a key at index to new value
        """

        self.heap[index] = new_value
        while i != 0 and self.heap[self.parent(index)] > self.heap[index]:
            # Swap index with parent of index
            parent = self.parent[index]
            self.heap[index], self.heap[parent] = (
                self.heap[parent],
                self.heap[index]
            )

    def pop(self):
        return heappop(self.heap)

    def delete(self, index):
        self.dec(index, MINIMUM)
        return self.pop()

    def get(self):
        return self.heap[0]

class Encoder:
    def __init__(self, codes=["I"]):
        self.codes = codes
        self.code = "".join(self.codes)

    def read(self, data):
        return unpack(self.code, data)

    def write(self, data):
        args = list()
        for c, code in enumerate(self.codes):
            datum = data[c]
            if "s" in code and isinstance(datum, str):
                data[c] = datum.encode()

        return pack(self.code, *data)

class FileEntry():
    def __init__(self, name, index, offset, size, isdir=False):
        self.sector = None

        self.etype = 1 if isdir else 0
        self.attrs = 0
        self.ts = None

        self.index = index
        self.offset = offset

        if len(size) > pow(2, 16):
            raise ValueError("Size is too large")

        self.size = size

        if len(name) > 18:
            raise ValueError("Name is too long")

        self.name = name

    @staticmethod
    def init(cls, raw, obj=None):
        tape = list()
        for byte in raw:
            bits = self._encode(byte)
            tape = tape + bits

        entry = int(tape[0])
        if entry == 0:
            raise ValueError("Not a valid file entry")

        etype = int(tape[1])
        attrs = self._decode(tape[2:14])
        index = self._decode(tape[14:24])
        offset = self._decode(tape[24:32])
        size = self._decode(tape[32:48])
        ts = self._decode(tape[48:112])

        name = ""
        for byte in tape[112:]:
            if byte == 0:
                continue

            name = name + chr(byte)

        if obj is None:
            obj = FileEntry(name, index, offset, size, etype == 1)

        else:
            obj.etype = etype
            obj.attrs = attrs
            obj.index = index
            obj.offset = offset
            obj.size = size
            obj.name = name

        obj.ts = ts

        return obj

    def _encode(self, num, pad=None):
        bits = list(bin(byte)[2:])
        size = len(bits)
        if pad is not None:
            bits = leftpad(bits, pad)

        else:
            mod = size % 8
            if mod != 0:
                bits = leftpad(bits, size + (8 - mod))

        return bits

    def _decode(self, bits):
        return int("".join(bits, 2))

    def attach(self, sector):
        self.sector = sector

    def attr(self, attr):
        self.attrs = self.attrs ^ attr

    def load(self):
        raw = self.sector.read(self.offset, self.size)
        FileEntry.init(raw, self)

    def save(self):
        self.ts = int(time())

        tape = ["0"] * 32
        tape[0] = "1"
        tape[1] = "1" if self.etype else "0"

        tape[2:14] = self._encode(self.attrs, 12)
        tape[14:24] = self._encode(self.index, 10)
        tape[24:32] = self._encode(self.offset, 8)
        tape[32:48] = self._encode(self.size, 16)
        tape[48:112] = self._encode(self.ts, 64)

        name = list()
        for letter in name:
            name.append(ord(letter))

        tape[112:] = leftpad(name, 18, 0)

        raw = list()
        for i in range(32):
            byte = self._decode(tape[i*8:(i+1)*8])
            raw.append(byte)

        return raw
