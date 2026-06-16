import heapq
import pickle
from collections import Counter


class Node:
    def __init__(self, byte, freq):
        self.byte = byte
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


def build_tree(data):
    freq = Counter(data)

    heap = []

    for byte, count in freq.items():
        heapq.heappush(heap, Node(byte, count))

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)

        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right

        heapq.heappush(heap, merged)

    return heap[0]


def build_codes(node, code="", codes=None):
    if codes is None:
        codes = {}

    if node.byte is not None:
        codes[node.byte] = code
        return codes

    build_codes(node.left, code + "0", codes)
    build_codes(node.right, code + "1", codes)

    return codes


def compress_file(input_file, output_file):

    with open(input_file, "rb") as f:
        data = f.read()

    tree = build_tree(data)
    codes = build_codes(tree)

    encoded = "".join(codes[b] for b in data)

    padding = 8 - len(encoded) % 8
    encoded += "0" * padding

    byte_array = bytearray()

    for i in range(0, len(encoded), 8):
        byte_array.append(int(encoded[i:i+8], 2))

    with open(output_file, "wb") as f:
        pickle.dump((codes, padding), f)
        f.write(byte_array)

    return len(data), len(byte_array)


def decompress_file(input_file, output_file):

    with open(input_file, "rb") as f:
        codes, padding = pickle.load(f)
        compressed = f.read()

    reverse_codes = {v: k for k, v in codes.items()}

    bits = ""

    for byte in compressed:
        bits += format(byte, "08b")

    bits = bits[:-padding]

    decoded = bytearray()
    current = ""

    for bit in bits:
        current += bit

        if current in reverse_codes:
            decoded.append(reverse_codes[current])
            current = ""

    with open(output_file, "wb") as f:
        f.write(decoded)