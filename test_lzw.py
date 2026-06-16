from algorithms.lzw import (
    compress_file,
    decompress_file
)

original = "bmp_dataset/img1.bmp"

compressed = "compressed/img1_lzw.bin"

decompressed = "decompressed/img1_lzw.bmp"

before, after = compress_file(
    original,
    compressed
)

decompress_file(
    compressed,
    decompressed
)

print("Ukuran awal :", before, "bytes")
print("Ukuran akhir:", after, "bytes")

percent = ((before - after) / before) * 100

print(f"Pengurangan: {percent:.2f}%")