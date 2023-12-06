#from ewenix.structure import MinHeap
from math import log, ceil

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

    def unalloc(self, pointer):
        address = self.pointers.get(pointer)
        if address is None:
            return True, f"Cannot free unallocated address: {pointer}"

        query = ceil(log(address) / log(2))
        self.free[query].append(Span(pointer, pointer + pow(2, query) -1))

        buddy = pointer / address
        if buddy % 2 == 0:
            baddress = pointer + pow(2, query)

        else:
            baddress = pointer - pow(2, query)

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
                    baddress,
                    baddress + 2 * (pow(2, query)-1)
                ))

            self.free[query].pop(i)
            self.free[query].pop(len(self.free[query])-1)
            break

        self.pointers.pop(pointer, None)
        return False, None

    def allocated(self, pointer):
        return self.pointers.get(pointer) is not None

class Memory:
    def __init__(self, size):
        self.size = size
        self.block = 32
        self.offset = 128

        self.clear()

    def clear(self):
        self.mem = [0] * self.size
        self.blocks = Buddy(self.size // self.block)
        self.owners = dict()

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

        if not self.blocks.allocated:
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
