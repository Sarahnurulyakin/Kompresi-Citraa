import os
import pandas as pd

from algorithms.rle import compress_file as rle_compress
from algorithms.lzw import compress_file as lzw_compress
from algorithms.huffman import compress_file as huffman_compress

DATASET = "bmp_dataset"

results = []

for file in os.listdir(DATASET):

    if not file.endswith(".bmp"):
        continue

    path = os.path.join(DATASET, file)

    algorithms = {
        "RLE": rle_compress,
        "LZW": lzw_compress,
        "Huffman": huffman_compress
    }

    for algo_name, algo_func in algorithms.items():

        output = os.path.join(
            "compressed",
            f"{os.path.splitext(file)[0]}_{algo_name}.bin"
        )

        before, after = algo_func(path, output)

        percent = ((before - after) / before) * 100

        results.append({
            "Gambar": file,
            "Algoritma": algo_name,
            "Ukuran Awal (Byte)": before,
            "Ukuran Akhir (Byte)": after,
            "Persentase (%)": round(percent, 2)
        })

        print(
            f"{file} | {algo_name} | {percent:.2f}%"
        )

df = pd.DataFrame(results)

df.to_csv(
    "hasil_kompresi.csv",
    index=False
)

print("\n===== RATA-RATA =====")

avg = df.groupby(
    "Algoritma"
)["Persentase (%)"].mean()

print(avg)

print("\nSelesai!")
print("File disimpan: hasil_kompresi.csv")