import os
import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from algorithms.rle import compress_file as rle_compress
from algorithms.rle import decompress_file as rle_decompress

from algorithms.lzw import compress_file as lzw_compress
from algorithms.lzw import decompress_file as lzw_decompress

from algorithms.huffman import compress_file as huffman_compress
from algorithms.huffman import decompress_file as huffman_decompress


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Aplikasi Kompresi Citra")
        self.geometry("1200x800")

        ctk.set_appearance_mode("light")

        self.file_path = None

        title = ctk.CTkLabel(
            self,
            text="Studi Komparasi Algoritma Kompresi Citra",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=10)

        # Tombol pilih gambar
        self.btn_open = ctk.CTkButton(
            self,
            text="Pilih Gambar BMP",
            command=self.open_image
        )
        self.btn_open.pack(pady=5)

        # Pilihan algoritma
        self.algorithm = ctk.StringVar(value="LZW")

        self.option = ctk.CTkOptionMenu(
            self,
            values=["RLE", "LZW", "Huffman"],
            variable=self.algorithm
        )
        self.option.pack(pady=5)

        # Tombol kompres
        self.btn_compress = ctk.CTkButton(
            self,
            text="Kompresi",
            command=self.compress_image
        )
        self.btn_compress.pack(pady=5)
        self.btn_batch = ctk.CTkButton(
            self,
            text="Uji Semua Dataset (90 Pengujian)",
            command=self.batch_test
        )
        self.btn_batch.pack(pady=5)

        # Frame gambar
        self.frame_images = ctk.CTkFrame(self)
        self.frame_images.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        self.lbl_original = ctk.CTkLabel(
            self.frame_images,
            text="Gambar Asli",
            width=400,
            height=400
        )
        self.lbl_original.grid(
            row=0,
            column=0,
            padx=20,
            pady=20
        )

        self.lbl_result = ctk.CTkLabel(
            self.frame_images,
            text="Gambar Hasil Dekompresi",
            width=400,
            height=400
        )
        self.lbl_result.grid(
            row=0,
            column=1,
            padx=20,
            pady=20
        )

        # Informasi
        self.info = ctk.CTkTextbox(
            self,
            width=1000,
            height=200
        )
        self.info.pack(pady=10)

        self.batch_box = ctk.CTkTextbox(
            self,
            width=1000,
            height=250
        )

        self.batch_box.pack(
            padx=10,
            pady=10,
            fill="both",
            expand=True
        )

    def show_image(self, label, path):

        img = Image.open(path)
        img.thumbnail((350, 350))

        photo = ImageTk.PhotoImage(img)

        label.configure(
            image=photo,
            text=""
        )

        label.image = photo

    def open_image(self):

        file_path = filedialog.askopenfilename(
            initialdir="bmp_dataset",
            filetypes=[("BMP", "*.bmp")]
        )

        if not file_path:
            return

        self.file_path = file_path

        self.show_image(
            self.lbl_original,
            file_path
        )

        size = os.path.getsize(file_path)

        self.info.delete("1.0", "end")

        self.info.insert(
            "end",
            f"File : {os.path.basename(file_path)}\n"
        )

        self.info.insert(
            "end",
            f"Ukuran Awal : {size/1024:.2f} KB\n"
        )

    def compress_image(self):

        if self.file_path is None:
            messagebox.showwarning(
                "Peringatan",
                "Pilih gambar terlebih dahulu."
            )
            return

        algorithm = self.algorithm.get()

        filename = os.path.splitext(
            os.path.basename(self.file_path)
        )[0]

        compressed_file = os.path.join(
            "compressed",
            f"{filename}_{algorithm}.bin"
        )

        decompressed_file = os.path.join(
            "decompressed",
            f"{filename}_{algorithm}.bmp"
        )

        if algorithm == "RLE":

            before, after = rle_compress(
                self.file_path,
                compressed_file
            )

            rle_decompress(
                compressed_file,
                decompressed_file
            )

        elif algorithm == "LZW":

            before, after = lzw_compress(
                self.file_path,
                compressed_file
            )

            lzw_decompress(
                compressed_file,
                decompressed_file
            )

        else:

            before, after = huffman_compress(
                self.file_path,
                compressed_file
            )

            huffman_decompress(
                compressed_file,
                decompressed_file
            )

        percent = (
            (before - after) / before
        ) * 100

        self.show_image(
            self.lbl_result,
            decompressed_file
        )

        self.info.delete("1.0", "end")

        self.info.insert(
            "end",
            f"File              : {filename}.bmp\n"
        )

        self.info.insert(
            "end",
            f"Algoritma         : {algorithm}\n"
        )

        self.info.insert(
            "end",
            f"Ukuran Awal       : {before/1024:.2f} KB\n"
        )

        self.info.insert(
            "end",
            f"Ukuran Kompresi   : {after/1024:.2f} KB\n"
        )

        self.info.insert(
            "end",
            f"Pengurangan       : {percent:.2f}%\n"
        )

        self.info.insert(
            "end",
            f"\nFile kompresi disimpan di:\n{compressed_file}"
        )

    def batch_test(self):

        dataset = "bmp_dataset"

        results = []

        algorithms = {
            "RLE": rle_compress,
            "LZW": lzw_compress,
            "Huffman": huffman_compress
        }

        self.batch_box.delete("1.0", "end")

        self.batch_box.insert(
            "end",
            "Memulai pengujian 30 gambar × 3 algoritma...\n\n"
        )

        self.update()

        for file in os.listdir(dataset):

            if not file.endswith(".bmp"):
                continue

            path = os.path.join(dataset, file)

            for algo_name, algo_func in algorithms.items():

                output = os.path.join(
                    "compressed",
                    f"{os.path.splitext(file)[0]}_{algo_name}.bin"
                )

                before, after = algo_func(
                    path,
                    output
                )

                percent = (
                    (before - after) / before
                ) * 100

                results.append({
                    "Gambar": file,
                    "Algoritma": algo_name,
                    "Awal": before,
                    "Akhir": after,
                    "Persentase": percent
                })

                self.batch_box.insert(
                    "end",
                    f"{file:10} | "
                    f"{algo_name:8} | "
                    f"{before/1024:8.2f} KB | "
                    f"{after/1024:8.2f} KB | "
                    f"{percent:7.2f}%\n"
                )

                self.batch_box.see("end")
                self.update()

        df = pd.DataFrame(results)

        df.to_csv(
            "hasil_kompresi.csv",
            index=False
        )

        avg = df.groupby(
            "Algoritma"
        )["Persentase"].mean()

        self.batch_box.insert(
            "end",
            "\n==============================\n"
        )

        self.batch_box.insert(
            "end",
            "RATA-RATA KOMPRESI\n"
        )

        self.batch_box.insert(
            "end",
            "==============================\n"
        )

        for algo, value in avg.items():

            self.batch_box.insert(
                "end",
                f"{algo:10}: {value:.2f}%\n"
            )

        self.batch_box.insert(
            "end",
            "\nCSV berhasil disimpan:\nhasil_kompresi.csv\n"
        )

        messagebox.showinfo(
            "Selesai",
            "Pengujian 90 data selesai!"
        )