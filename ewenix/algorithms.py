from ewenix.structure import FileEntry, Encoder

from math import log, ceil
from pathlib import Path
from collections import namedtuple

Block = namedtuple("Block", [
    "sector",
    "offset",
    "size"
])

def bubble(xs, j=None, key=None):
    i = 0
    while i < len(xs)-1:
        xi = xs[i]
        xi1 = xs[i+1]

        if j is not None:
            xi = xi[j]
            xi1 = xi1[j]

        elif key is not None:
            xi = xi[key]
            xi1 = xi1[key]

        if xi <= xi1:
            i = i + 1
            continue

        xs[i], xs[i+1] = xs[i+1], xs[i]
        if i > 0:
            i = i-1

    return xs

class Span:
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

    def __repr__(self):
        return f"Span<{self.start},{self.stop}>"

class Buddy:
    def __init__(self, size):
        self.size = size
        self.clear()

    def clear(self):
        power = ceil(log(self.size) / log(2))
        self.free = list()

        for i in range(power+1):
            self.free.append(list())

        self.free[power].append(Span(0, self.size-1))
        self.pointers = dict()

    def alloc(self, size):
        query = ceil(log(size) / log(2))
        if query > len(self.free):
            return True, "Out of bounds exception (1)"

        if len(self.free[query]) > 0:
            temp = self.free[query].pop(0)
            self.pointers[temp.start] = temp.stop - temp.start + 1
            return False, temp

        index = None
        for i in range(query+1, len(self.free)):
            if len(self.free[i]) == 0:
                continue

            index = i
            break

        if index is None:
            return True, "Not enough memory to allocate"

        temp = self.free[index].pop(0)

        for i in range(index-1, query-1, -1):
            # Split the span in half
            span1 = Span(
                temp.start,
                temp.start + (temp.stop - temp.start) // 2
            )
            span2 = Span(
                temp.start + (temp.stop - temp.start + 1) // 2,
                temp.stop
            )

            # Add spans to the free blocks
            self.free[i].append(span1)
            self.free[i].append(span2)

            # Remove a block for the next pass down
            temp = self.free[i].pop(0)

        self.pointers[temp.start] = temp.stop - temp.start + 1
        return False, temp

    def unalloc(self, pointer, psize=None):
        size = self.pointers.get(pointer)
        if address is None:
            if psize is None:
                return True, f"Cannot free unallocated address: {pointer}"

            # NOTE - Used when the pointer size is known in advance
            for ptr, sze in self.pointers.items():
                if pointer < ptr or pointer > ptr + sze:
                    continue

                # Removes the existing pointer
                self.unalloc(ptr)

                # Create new entries split up from
                self.load(ptr, pointer-1)
                self.load(pointer, pointer+psize-1)
                if pointer+psize-1 != ptr+sze-1:
                    self.load(pointer+psize, ptr+sze-1)

        query = ceil(log(size) / log(2))
        self.free[query].append(Span(pointer, pointer + pow(2, query)-1))

        buddy = pointer / size
        if buddy % 2 == 0:
            ppointer = pointer + pow(2, query)

        else:
            ppointer = pointer - pow(2, query)

        for i in range(len(self.free[query])):
            # Buddy is not free
            if self.free[query][i].start != baddress:
                continue

            if buddy % 2 == 0:
                # Buddy is the block after the block with this address
                self.free[query+1].append(Span(
                    pointer,
                    pointer + 2 * (pow(2, query)-1)
                ))

            else:
                # Buddy is the block before the block with this address
                self.free[query+1].append(Span(
                    ppointer,
                    ppointer + 2 * (pow(2, query)-1)
                ))

            self.free[query].pop(i)
            self.free[query].pop(len(self.free[query])-1)
            break

        self.pointers.pop(pointer, None)
        return False, None

    def load(self, start, stop):
        span = Span(start, stop)
        size = stop - start + 1

        index = ceil(log(size) / log(2))
        self.free[index].append(span)
        self.pointers[start] = size

    def allocated(self, pointer):
        return self.pointers.get(pointer) is not None

class Memory:
    def __init__(self, size):
        self.size = size
        self.block = 32
        self.offset = 128

        self.clear()

    def clear(self):
        self.owners = dict()

        self.mem = [0] * self.size
        self.blocks = Buddy(self.size // self.block)

        # Reserve the first 128 bytes
        self.blocks.alloc(self.offset // self.block, jobid=-1)

    def assign(self, start, left, value):
        k = start // 8
        o = start % 8

        while left > 0:
            byte = self.mem[k]
            bits = list(bin(byte)[2:])
            if len(bits) < 8:
                bits = (["0"] * (8-len(bits))) + bits

            l = left if left < 8 else 8-o
            left = left - l
            for i in range(l):
                bits[i+o] = value

            self.mem[k] = int("".join(bits), 2)
            if left > 0:
                k = k+1
                o = 0

    def alloc(self, size, jobid=None):
        error, result = self.blocks.alloc(size)
        if error:
            return True, result

        span = result
        left = self.blocks.pointers.get(span.start)
        self.assign(span.start, left, "1")

        address = span.start * self.block
        uaddress = address + self.offset
        self.owners[uaddress] = jobid
        return False, uaddress

    def free(self, address, jobid=None):
        if self.owners.get(address) != jobid:
            return True, "Unauthorized memory address"

        pointer = (address - self.offset) // self.block
        left = self.blocks.pointers.get(pointer)

        error, result = self.blocks.unalloc(pointer)
        if error:
            return True, result

        self.assign(pointer, left, "0")
        self.owners.pop(address, None)
        return False, result

    def write(self, address, data, jobid=None):
        if address == -1:
            size = ceil(len(data) / self.block)
            error, result = self.alloc(size, jobid=jobid)
            if error:
                return True, result

            address = result
            print(f"Dynamically allocated address: {address}")

        if not self.blocks.allocated(address):
            return True, "Address is not allocated"

        if self.owners.get(address) != jobid:
            return True, "Unauthorized memory address"

        for i in range(len(data)):
            byte = data[i]
            if byte < 0 or byte > 255:
                return True, f"{byte} is out of bounds"

            self.mem[address+i] = byte

        return False, address

    def read(self, address, size, jobid=None):
        if address + size > len(self.mem):
            return True, "Out of bounds exception (2)"

        if self.owners.get(address) != jobid:
            return True, "Unauthorized memory address (1)"

        pointer = (address - self.offset) // self.block
        psize = self.blocks.pointers.get(pointer)
        if psize is None or psize * self.block < size:
            return True, "Unauthorized memory address (2)"

        return False, self.mem[address:address+size]

class Sector:
    def __init__(self, size, path):
        self.size = size
        self.path = path

        self.encoder = Encoder(["B"] * self.size)

    def clear(self):
        self.raw = [0] * self.size

        self.pull()

    def push(self):
        self.path.write_bytes(self.encoder.write(self.raw))

    def pull(self):
        data = self.encoder.read(self.path.read_bytes())
        for i, byte in enumerate(data):
            self.raw[i] = ord(byte)

        # Pull the reserved bits for allocation
        reserved = (self.size // self.block) // 8
        allocation = self.raw[:reserved]

        # Load in the pre-existing allocations
        for byte in allocation:
            bits = list(bin(byte)[2:])
            if len(bits) < 8:
                bits = (["0"] * (8-len(bits))) + bits

            for bit in bits:
                if bit == "1":
                    s = s + 1
                    continue

                if s > 0:
                    self.blocks.alloc(s)
                    s = 0

            if s > 0:
                self.blocks.alloc(s)

    def write(self, address, data):
        size = len(data)
        for i in range(size):
            byte = data[i]
            if byte < 0 or byte > 255:
                return True, f"{byte} is out of bounds"

            self.raw[address+i] = byte

        return False, address

    def read(self, address, size):
        if address + size > len(self.raw):
            return True, "Out of bounds exception"

        return False, self.raw[address:address+size]

class Storage:
    def __init__(self, sectors, size, root=None):
        self.sector_count = sectors
        self.sector_size = size
        self.root = None

    def clear(self):
        if self.root is None:
            self.root = Path.cwd() / "store"

        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)

        self.sectors = list()
        for i in range(self.sector_count):
            path = self.root / f"{i}.bin"
            sector = Sector(self.sector_size, path)
            self.sectors.append(rsector)

    #def alloc(self, size):
    #    error, result = self.raw.alloc(size)
    #    if error:
    #        return True, result

    #    span = result
    #    address = span.start

    #    sector_index = address // self.sector_size
    #    sector_offset = address % self.sector_size

    #    cache = None
    #    while True:
    #        sector = self.sectors[sector_index]
    #        sector_left = sector.size - sector_offset
    #        if len(data) > sector_left:
    #            data, cache = data[:sector_left], data[sector_left:]

    #        sector.write(sector_offset, data)
    #        if cache is None:
    #            break

    #        sector_index = sector_index + 1
    #        sector_offset = 0
    #        data = cache
    #        cache = None

    #    return False, address

    def write(self, address, data):
        #if not self.raw.allocated(address):
        #    return True, "Address is not allocated"

        #if len(data) > self.raw.pointers.get(address, 0):
        #    return True, "Out of bounds exception (1)"

        sector_index = address // self.sector_size
        sector_offset = address % self.sector_size

        cache = None
        while True:
            sector = self.sectors[sector_index]
            sector_left = sector.size - sector_offset
            if len(data) > sector_left:
                data, cache = data[:sector_left], data[sector_left:]

            sector.write(sector_offset, data)
            if cache is None:
                break

            sector_index = sector_index + 1
            sector_offset = 0
            data = cache
            cache = None

        return False, address

    def read(self, address, size):
        sector_index = address // self.sector_size
        sector_offset = address % self.sector_size

        read = list()
        while size > 0:
            sector = self.sectors[sector_index]
            sector_left = sector.size - sector_offset
            request = size
            if size > sector_left:
                request = sector_left
                size = size - sector_left

            else:
                size = 0

            error, result = sector.read(sector_offset, request)
            if error:
                return True, result

            if read is not None:
                read = read + result

            sector_index = sector_index + 1
            sector_offset = 0

        return False, read

class FileSystem:
    def __init__(self, storage, size):
        self.storage = storage
        self.size = size

        self.block = 32

        self.st_offset = 128 # Sector offset
        self.se_offset = 32 # Bytes offset in sector

        self.clear()

    def clear(self):
        self.storage.clear()
        self.load()

    def load(self):
        index = 0
        cache = None
        blocks = dict()

        self.table = list()
        for sector in self.storage.sectors:
            sector.pull()

            table = dict()
            error, result = sector.read(4, 28)
            if error:
                return True, result

            count = 0
            block = 0
            start = None
            for byte in result:
                bits = list(bin(byte)[2:])
                for bit in bits:
                    free = bit == "0"
                    if free:
                        block = block + 1
                        if start is None:
                            start = count

                    elif not free and block > 0:
                        table[start+32] = block
                        blocks[(index, start+32)] = block

                        start = None
                        block = 0

                        if cache is not None:
                            c_index, c_start, c_block = cache
                            blocks[(c_index, c_start)] = c_block + block
                            cache = None

                    count = count + 1

            if block > 0:
                cache = index, start+32, block

            index = index + 1
            self.table.append(table)

        self.blocks = list()
        for (index, start), block in blocks.items():
            self.blocks.append(Block(index, start, block))

        bubble(self.blocks, "size")

        self.fblocks = list()
        for i in range(self.st_offset):
            sector = self.storage.sectors[i]

            for j in range(sector.size // self.se_offset):
                address = j * self.se_offset
                entry = sector.read(address, self.se_offset)

                # Detect if file system entry is set or not
                if entry[0] < 128:
                    self.fblocks.append(None)
                    continue

                fblock = FileEntry.init(entry)
                fblock.attach(sector)
                self.fblocks.append(fblock)

