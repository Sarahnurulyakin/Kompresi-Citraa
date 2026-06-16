from PIL import Image
import os

input_folder = "dataset"
output_folder = "bmp_dataset"

os.makedirs(output_folder, exist_ok=True)

for file in os.listdir(input_folder):

    if file.lower().endswith(".png"):
        try:
            path = os.path.join(input_folder, file)

            img = Image.open(path)
            img.verify()  # verifikasi file

            img = Image.open(path)

            filename = os.path.splitext(file)[0]
            output_path = os.path.join(
                output_folder,
                filename + ".bmp"
            )

            img.save(output_path, "BMP")

            print(f"✓ {file} -> {filename}.bmp")

        except Exception as e:
            print(f"✗ Gagal memproses {file}: {e}")

print("Konversi selesai.")