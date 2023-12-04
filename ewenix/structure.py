from heapq import heappush, heappop, heapify

MINIMUM = float("-inf")

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
