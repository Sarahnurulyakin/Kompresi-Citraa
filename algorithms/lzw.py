import struct

MAX_DICT_SIZE = 65535


def compress(data):
    """
    Kompres data menggunakan algoritma LZW
    """
    dictionary = {bytes([i]): i for i in range(256)}
    dict_size = 256

    w = b""
    result = []

    for c in data:
        wc = w + bytes([c])

        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])

            # Tambahkan ke dictionary jika belum penuh
            if dict_size < MAX_DICT_SIZE:
                dictionary[wc] = dict_size
                dict_size += 1

            w = bytes([c])

    if w:
        result.append(dictionary[w])

    return result


def decompress(compressed):
    """
    Dekompresi data LZW
    """
    dictionary = {i: bytes([i]) for i in range(256)}
    dict_size = 256

    if not compressed:
        return bytearray()

    w = bytes([compressed.pop(0)])
    result = bytearray(w)

    for k in compressed:

        if k in dictionary:
            entry = dictionary[k]

        elif k == dict_size:
            entry = w + w[:1]

        else:
            raise ValueError("Data LZW tidak valid")

        result.extend(entry)

        if dict_size < MAX_DICT_SIZE:
            dictionary[dict_size] = w + entry[:1]
            dict_size += 1

        w = entry

    return result


def compress_file(input_file, output_file):
    """
    Kompres file
    """
    with open(input_file, "rb") as f:
        data = f.read()

    compressed = compress(data)

    with open(output_file, "wb") as f:
        for code in compressed:
            f.write(struct.pack(">H", code))

    original_size = len(data)
    compressed_size = len(compressed) * 2

    return original_size, compressed_size


def decompress_file(input_file, output_file):
    """
    Dekompresi file
    """
    compressed = []

    with open(input_file, "rb") as f:

        while True:
            bytes_read = f.read(2)

            if not bytes_read:
                break

            compressed.append(
                struct.unpack(">H", bytes_read)[0]
            )

    decompressed = decompress(compressed)

    with open(output_file, "wb") as f:
        f.write(decompressed)