import os


def compress(data):
    """
    Kompres data byte menggunakan RLE
    """
    if not data:
        return bytearray()

    compressed = bytearray()

    count = 1
    prev = data[0]

    for current in data[1:]:

        if current == prev and count < 255:
            count += 1
        else:
            compressed.append(count)
            compressed.append(prev)

            prev = current
            count = 1

    compressed.append(count)
    compressed.append(prev)

    return compressed


def decompress(compressed_data):
    """
    Dekompresi data RLE
    """

    decompressed = bytearray()

    for i in range(0, len(compressed_data), 2):
        count = compressed_data[i]
        value = compressed_data[i + 1]

        decompressed.extend([value] * count)

    return decompressed


def compress_file(input_file, output_file):

    with open(input_file, "rb") as f:
        data = f.read()

    compressed = compress(data)

    with open(output_file, "wb") as f:
        f.write(compressed)

    return len(data), len(compressed)


def decompress_file(input_file, output_file):

    with open(input_file, "rb") as f:
        compressed_data = f.read()

    decompressed = decompress(compressed_data)

    with open(output_file, "wb") as f:
        f.write(decompressed)