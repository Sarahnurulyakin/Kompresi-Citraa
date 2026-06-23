import os
import time
import customtkinter as ctk
import pandas as pd
import numpy as np
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import compression/decompression functions
from algorithms.rle import compress_file as rle_compress
from algorithms.rle import decompress_file as rle_decompress
from algorithms.lzw import compress_file as lzw_compress
from algorithms.lzw import decompress_file as lzw_decompress
from algorithms.huffman import compress_file as huffman_compress
from algorithms.huffman import decompress_file as huffman_decompress


def get_hex_dump(file_path, max_bytes=48):
    """
    Membaca file biner dan memformatnya menjadi string Hex Dump.
    """
    if not file_path or not os.path.exists(file_path):
        return "File tidak ditemukan"
    try:
        with open(file_path, "rb") as f:
            data = f.read(max_bytes)
        if not data:
            return "File kosong"
        
        hex_dump = []
        for i in range(0, len(data), 8):
            chunk = data[i:i+8]
            hex_str = " ".join(f"{b:02X}" for b in chunk)
            if len(chunk) < 8:
                hex_str = hex_str.ljust(23)
            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            hex_dump.append(f"{hex_str}  | {ascii_str}")
            
        return "\n".join(hex_dump)
    except Exception as e:
        return f"Error: {str(e)}"


def get_image_details(file_path):
    """
    Mengambil metadata gambar BMP menggunakan Pillow.
    """
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        with Image.open(file_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "size": os.path.getsize(file_path)
            }
    except Exception:
        return None


def calculate_metrics(original_path, decompressed_path):
    """
    Menghitung MSE (Mean Squared Error) dan PSNR (Peak Signal-to-Noise Ratio)
    antara gambar original dan decompressed.
    """
    try:
        if not original_path or not os.path.exists(original_path):
            return {"mse": None, "psnr": None}
        if not decompressed_path or not os.path.exists(decompressed_path):
            return {"mse": None, "psnr": None}
            
        with Image.open(original_path) as img1, Image.open(decompressed_path) as img2:
            img1_rgb = img1.convert("RGB")
            img2_rgb = img2.convert("RGB")
            
            if img1_rgb.size != img2_rgb.size:
                return {"mse": -1.0, "psnr": -1.0}
                
            arr1 = np.array(img1_rgb, dtype=np.float64)
            arr2 = np.array(img2_rgb, dtype=np.float64)
            
            mse = np.mean((arr1 - arr2) ** 2)
            if mse == 0:
                psnr = float('inf')
            else:
                max_pixel = 255.0
                psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
                
            return {"mse": mse, "psnr": psnr}
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return {"mse": None, "psnr": None}


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Aplikasi Kompresi Citra BMP - Premium Edition")
        self.geometry("1300x880")
        self.minsize(1100, 768)

        # Set tema tampilan bawaan
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.file_path = None
        self.single_results = None
        self.batch_df = None

        # Memuat CSV hasil kompresi jika sudah ada
        if os.path.exists("hasil_kompresi.csv"):
            try:
                self.batch_df = pd.read_csv("hasil_kompresi.csv")
                # Pastikan kolom waktu ada
                if "Waktu_Kompresi" not in self.batch_df.columns:
                    self.batch_df["Waktu_Kompresi"] = 0.0
                if "Waktu_Dekompresi" not in self.batch_df.columns:
                    self.batch_df["Waktu_Dekompresi"] = 0.0
            except Exception as e:
                print(f"Gagal membaca hasil_kompresi.csv pada startup: {e}")

        # Konfigurasi tata letak grid utama
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Inisialisasi komponen UI
        self.setup_sidebar()
        self.setup_main_area()

    def setup_sidebar(self):
        # Frame Sidebar
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=("#ebebeb", "#16161a"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)  # Spacer row

        # Logo / Judul
        self.lbl_logo = ctk.CTkLabel(
            self.sidebar, 
            text="⚙️ KOMPRESI CITRA", 
            font=("Segoe UI", 20, "bold"),
            text_color=("#1e293b", "#f8fafc")
        )
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.lbl_sublogo = ctk.CTkLabel(
            self.sidebar, 
            text="Studi Komparasi Algoritma", 
            font=("Segoe UI", 12, "italic"),
            text_color=("#64748b", "#94a3b8")
        )
        self.lbl_sublogo.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Garis Pembatas
        self.sep = ctk.CTkFrame(self.sidebar, height=2, fg_color=("#cbd5e1", "#334155"))
        self.sep.grid(row=2, column=0, padx=15, pady=0, sticky="ew")

        # Tombol Pilih Gambar
        self.btn_open = ctk.CTkButton(
            self.sidebar,
            text="📁 Pilih Gambar BMP",
            font=("Segoe UI", 13, "bold"),
            fg_color="#5b5fc7",
            hover_color="#4a4db0",
            command=self.open_image
        )
        self.btn_open.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

        # Kartu Detail Gambar Asli
        self.card_details = ctk.CTkFrame(self.sidebar, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_details.grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        
        self.lbl_details_title = ctk.CTkLabel(
            self.card_details, 
            text="Detail Gambar Asli", 
            font=("Segoe UI", 13, "bold"),
            text_color=("#1e293b", "#f8fafc")
        )
        self.lbl_details_title.pack(anchor="w", padx=15, pady=(10, 5))

        self.lbl_details_text = ctk.CTkLabel(
            self.card_details,
            text="Belum ada gambar yang dipilih.\nSilakan klik tombol di atas.",
            font=("Segoe UI", 12),
            text_color=("#64748b", "#94a3b8"),
            justify="left"
        )
        self.lbl_details_text.pack(anchor="w", padx=15, pady=(0, 15))

        # Tombol Eksekusi Kompresi
        self.btn_compress = ctk.CTkButton(
            self.sidebar,
            text="⚡ Jalankan Kompresi",
            font=("Segoe UI", 13, "bold"),
            fg_color="#10b981",
            hover_color="#059669",
            state="disabled",
            command=self.compress_image
        )
        self.btn_compress.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        # Tombol Uji Massal (Dataset)
        self.btn_batch = ctk.CTkButton(
            self.sidebar,
            text="📊 Uji Dataset (90 Tes)",
            font=("Segoe UI", 13, "bold"),
            fg_color=("#64748b", "#334155"),
            hover_color=("#475569", "#1e293b"),
            command=self.switch_to_batch_tab
        )
        self.btn_batch.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        # Switcher Mode Gelap / Terang
        self.switch_theme_var = ctk.StringVar(value="dark")
        self.switch_theme = ctk.CTkSwitch(
            self.sidebar,
            text="Mode Gelap",
            font=("Segoe UI", 12),
            variable=self.switch_theme_var,
            onvalue="dark",
            offvalue="light",
            command=self.toggle_theme
        )
        self.switch_theme.grid(row=8, column=0, padx=20, pady=20, sticky="s")

    def setup_main_area(self):
        # Tabview untuk Workspace Utama
        self.tabview = ctk.CTkTabview(self, corner_radius=10, fg_color=("#ffffff", "#121214"))
        self.tabview.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        self.tabview.add("Kompresi Tunggal")
        self.tabview.add("Analisis Dataset")
        self.tabview.add("Visualisasi Grafik")

        # Setup Tab 1, Tab 2, & Tab 3
        self.setup_tab_single()
        self.setup_tab_batch()
        self.setup_tab_charts()

    def setup_tab_single(self):
        tab = self.tabview.tab("Kompresi Tunggal")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=3)  # Preview Frame
        tab.grid_rowconfigure(1, weight=2)  # Comparison Table Frame

        # Frame Panel Preview (Original vs Decompressed)
        self.previews_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.previews_frame.grid(row=0, column=0, pady=(10, 10), sticky="nsew")
        self.previews_frame.grid_columnconfigure(0, weight=1)
        self.previews_frame.grid_columnconfigure(1, weight=1)
        self.previews_frame.grid_columnconfigure(2, weight=1)
        self.previews_frame.grid_columnconfigure(3, weight=1)
        self.previews_frame.grid_rowconfigure(0, weight=1)

        # Kartu Gambar Original
        self.card_orig = ctk.CTkFrame(self.previews_frame, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_orig.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        
        lbl_orig_title = ctk.CTkLabel(
            self.card_orig, 
            text="🖼️ GAMBAR ASLI", 
            font=("Segoe UI", 12, "bold"), 
            text_color=("#1e293b", "#f8fafc")
        )
        lbl_orig_title.pack(pady=10)

        self.lbl_orig_preview = ctk.CTkLabel(
            self.card_orig, 
            text="Belum ada gambar", 
            width=200, 
            height=200, 
            fg_color=("#cbd5e1", "#16161a"), 
            corner_radius=8
        )
        self.lbl_orig_preview.pack(padx=10, pady=5, expand=True)

        self.lbl_orig_info = ctk.CTkLabel(self.card_orig, text="-", font=("Segoe UI", 11), text_color=("#64748b", "#94a3b8"))
        self.lbl_orig_info.pack(pady=(5, 10))

        # Kartu Gambar Huffman Decompressed
        self.card_huf = ctk.CTkFrame(self.previews_frame, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_huf.grid(row=0, column=1, padx=(5, 5), sticky="nsew")
        
        lbl_huf_title = ctk.CTkLabel(
            self.card_huf, 
            text="⚡ HUFFMAN COMPRESSION", 
            font=("Segoe UI", 11, "bold"), 
            text_color=("#1e293b", "#f8fafc")
        )
        lbl_huf_title.pack(pady=(8, 2))

        lbl_huf_hex_title = ctk.CTkLabel(self.card_huf, text="Hex Viewer (.bin)", font=("Segoe UI", 9, "bold"), text_color=("#64748b", "#94a3b8"))
        lbl_huf_hex_title.pack(pady=0)

        self.lbl_huf_hex = ctk.CTkLabel(
            self.card_huf,
            text="Belum ada data",
            font=("Consolas", 8),
            height=65,
            fg_color=("#cbd5e1", "#090d16"),
            text_color=("#0f766e", "#10b981"),
            corner_radius=6,
            justify="left"
        )
        self.lbl_huf_hex.pack(padx=10, pady=(2, 4), fill="x")

        lbl_huf_dec_title = ctk.CTkLabel(self.card_huf, text="Hasil Dekompresi (.bmp)", font=("Segoe UI", 9, "bold"), text_color=("#64748b", "#94a3b8"))
        lbl_huf_dec_title.pack(pady=0)

        self.lbl_huf_preview = ctk.CTkLabel(
            self.card_huf, 
            text="Silakan jalankan kompresi", 
            width=90, 
            height=90, 
            fg_color=("#cbd5e1", "#16161a"), 
            corner_radius=8
        )
        self.lbl_huf_preview.pack(padx=10, pady=(2, 4))

        self.lbl_huf_info = ctk.CTkLabel(self.card_huf, text="-", font=("Segoe UI", 10), text_color=("#64748b", "#94a3b8"), justify="left")
        self.lbl_huf_info.pack(pady=(2, 8))

        # Kartu Gambar LZW Decompressed
        self.card_lzw = ctk.CTkFrame(self.previews_frame, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_lzw.grid(row=0, column=2, padx=(5, 5), sticky="nsew")
        
        lbl_lzw_title = ctk.CTkLabel(
            self.card_lzw, 
            text="⚡ LZW COMPRESSION", 
            font=("Segoe UI", 11, "bold"), 
            text_color=("#1e293b", "#f8fafc")
        )
        lbl_lzw_title.pack(pady=(8, 2))

        lbl_lzw_hex_title = ctk.CTkLabel(self.card_lzw, text="Hex Viewer (.bin)", font=("Segoe UI", 9, "bold"), text_color=("#64748b", "#94a3b8"))
        lbl_lzw_hex_title.pack(pady=0)

        self.lbl_lzw_hex = ctk.CTkLabel(
            self.card_lzw,
            text="Belum ada data",
            font=("Consolas", 8),
            height=65,
            fg_color=("#cbd5e1", "#090d16"),
            text_color=("#0f766e", "#10b981"),
            corner_radius=6,
            justify="left"
        )
        self.lbl_lzw_hex.pack(padx=10, pady=(2, 4), fill="x")

        lbl_lzw_dec_title = ctk.CTkLabel(self.card_lzw, text="Hasil Dekompresi (.bmp)", font=("Segoe UI", 9, "bold"), text_color=("#64748b", "#94a3b8"))
        lbl_lzw_dec_title.pack(pady=0)

        self.lbl_lzw_preview = ctk.CTkLabel(
            self.card_lzw, 
            text="Silakan jalankan kompresi", 
            width=90, 
            height=90, 
            fg_color=("#cbd5e1", "#16161a"), 
            corner_radius=8
        )
        self.lbl_lzw_preview.pack(padx=10, pady=(2, 4))

        self.lbl_lzw_info = ctk.CTkLabel(self.card_lzw, text="-", font=("Segoe UI", 10), text_color=("#64748b", "#94a3b8"), justify="left")
        self.lbl_lzw_info.pack(pady=(2, 8))

        # Kartu Gambar RLE Decompressed
        self.card_rle = ctk.CTkFrame(self.previews_frame, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_rle.grid(row=0, column=3, padx=(5, 0), sticky="nsew")
        
        lbl_rle_title = ctk.CTkLabel(
            self.card_rle, 
            text="⚡ RLE COMPRESSION", 
            font=("Segoe UI", 11, "bold"), 
            text_color=("#1e293b", "#f8fafc")
        )
        lbl_rle_title.pack(pady=(8, 2))

        lbl_rle_hex_title = ctk.CTkLabel(self.card_rle, text="Hex Viewer (.bin)", font=("Segoe UI", 9, "bold"), text_color=("#64748b", "#94a3b8"))
        lbl_rle_hex_title.pack(pady=0)

        self.lbl_rle_hex = ctk.CTkLabel(
            self.card_rle,
            text="Belum ada data",
            font=("Consolas", 8),
            height=65,
            fg_color=("#cbd5e1", "#090d16"),
            text_color=("#0f766e", "#10b981"),
            corner_radius=6,
            justify="left"
        )
        self.lbl_rle_hex.pack(padx=10, pady=(2, 4), fill="x")

        lbl_rle_dec_title = ctk.CTkLabel(self.card_rle, text="Hasil Dekompresi (.bmp)", font=("Segoe UI", 9, "bold"), text_color=("#64748b", "#94a3b8"))
        lbl_rle_dec_title.pack(pady=0)

        self.lbl_rle_preview = ctk.CTkLabel(
            self.card_rle, 
            text="Silakan jalankan kompresi", 
            width=90, 
            height=90, 
            fg_color=("#cbd5e1", "#16161a"), 
            corner_radius=8
        )
        self.lbl_rle_preview.pack(padx=10, pady=(2, 4))

        self.lbl_rle_info = ctk.CTkLabel(self.card_rle, text="-", font=("Segoe UI", 10), text_color=("#64748b", "#94a3b8"), justify="left")
        self.lbl_rle_info.pack(pady=(2, 8))

        # Tabel Perbandingan (Bawah)
        self.table_wrapper = ctk.CTkFrame(tab, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.table_wrapper.grid(row=1, column=0, pady=(10, 0), sticky="nsew")
        
        lbl_table_title = ctk.CTkLabel(
            self.table_wrapper, 
            text="📊 TABEL PERBANDINGAN ALGORITMA", 
            font=("Segoe UI", 14, "bold"), 
            text_color=("#1e293b", "#f8fafc")
        )
        lbl_table_title.pack(anchor="w", padx=15, pady=10)

        self.table_frame = ctk.CTkFrame(self.table_wrapper, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Setup grid kolom tabel
        for c in range(11):
            self.table_frame.grid_columnconfigure(c, weight=1)

        self.build_comparison_table()

    def build_comparison_table(self):
        # Hapus widget yang sudah ada
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        headers = [
            "Algoritma", "Ukuran Awal", "Ukuran Akhir", 
            "Rasio Kompresi", "Persentase Reduksi (%)", "Waktu Kompresi (ms)", 
            "Waktu Dekompresi (ms)", "Validasi Lossless", "MSE", "PSNR", "Status"
        ]

        for col_idx, h in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.table_frame, 
                text=h, 
                font=("Segoe UI", 11, "bold"), 
                text_color=("#475569", "#a0a0a5"),
                anchor="center"
            )
            lbl.grid(row=0, column=col_idx, padx=5, pady=8, sticky="nsew")

        self.table_cells = {}
        for row_idx, algo in enumerate(["RLE", "LZW", "Huffman"], start=1):
            self.table_cells[algo] = {}
            bg_color = ("#e2e8f0", "#16161a")

            self.table_cells[algo]["name"] = ctk.CTkLabel(self.table_frame, text=algo, font=("Segoe UI", 12, "bold"), fg_color=bg_color)
            self.table_cells[algo]["name"].grid(row=row_idx, column=0, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["original"] = ctk.CTkLabel(self.table_frame, text="-", font=("Consolas", 12), fg_color=bg_color)
            self.table_cells[algo]["original"].grid(row=row_idx, column=1, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["compressed"] = ctk.CTkLabel(self.table_frame, text="-", font=("Consolas", 12), fg_color=bg_color)
            self.table_cells[algo]["compressed"].grid(row=row_idx, column=2, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["ratio"] = ctk.CTkLabel(self.table_frame, text="-", font=("Consolas", 12), fg_color=bg_color)
            self.table_cells[algo]["ratio"].grid(row=row_idx, column=3, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["saving"] = ctk.CTkLabel(self.table_frame, text="-", font=("Consolas", 12, "bold"), fg_color=bg_color)
            self.table_cells[algo]["saving"].grid(row=row_idx, column=4, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["comp_time"] = ctk.CTkLabel(self.table_frame, text="-", font=("Consolas", 12), fg_color=bg_color)
            self.table_cells[algo]["comp_time"].grid(row=row_idx, column=5, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["dec_time"] = ctk.CTkLabel(self.table_frame, text="-", font=("Consolas", 12), fg_color=bg_color)
            self.table_cells[algo]["dec_time"].grid(row=row_idx, column=6, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["validation"] = ctk.CTkLabel(self.table_frame, text="-", font=("Segoe UI", 12), fg_color=bg_color)
            self.table_cells[algo]["validation"].grid(row=row_idx, column=7, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["mse"] = ctk.CTkLabel(self.table_frame, text="-", font=("Consolas", 12), fg_color=bg_color)
            self.table_cells[algo]["mse"].grid(row=row_idx, column=8, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["psnr"] = ctk.CTkLabel(self.table_frame, text="-", font=("Consolas", 12), fg_color=bg_color)
            self.table_cells[algo]["psnr"].grid(row=row_idx, column=9, padx=1, pady=1, sticky="nsew")

            self.table_cells[algo]["status"] = ctk.CTkLabel(self.table_frame, text="-", font=("Segoe UI", 12, "bold"), fg_color=bg_color)
            self.table_cells[algo]["status"].grid(row=row_idx, column=10, padx=1, pady=1, sticky="nsew")

    def setup_tab_batch(self):
        tab = self.tabview.tab("Analisis Dataset")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=0)  # Kontrol
        tab.grid_rowconfigure(1, weight=0)  # Progress Bar
        tab.grid_rowconfigure(2, weight=0)  # Summary Cards
        tab.grid_rowconfigure(3, weight=0)  # Filter
        tab.grid_rowconfigure(4, weight=1)  # Scrollable Table (expands)

        # Kontrol Atas
        control_frame = ctk.CTkFrame(tab, fg_color="transparent")
        control_frame.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        self.btn_run_batch = ctk.CTkButton(
            control_frame,
            text="▶️ Jalankan 90 Pengujian",
            font=("Segoe UI", 13, "bold"),
            fg_color="#5b5fc7",
            hover_color="#4a4db0",
            command=self.run_batch_test
        )
        self.btn_run_batch.pack(side="left", padx=10)

        self.batch_status_lbl = ctk.CTkLabel(
            control_frame, 
            text="Menunggu pengujian dijalankan...", 
            font=("Segoe UI", 12, "italic"),
            text_color=("#64748b", "#94a3b8")
        )
        self.batch_status_lbl.pack(side="left", padx=15)

        # Progress Bar
        self.batch_progress = ctk.CTkProgressBar(tab, height=10, fg_color=("#cbd5e1", "#334155"), progress_color="#10b981")
        self.batch_progress.grid(row=1, column=0, pady=5, padx=10, sticky="ew")
        self.batch_progress.set(0.0)

        # Summary Cards
        self.cards_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.cards_frame.grid(row=2, column=0, pady=10, sticky="ew")
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)
        self.cards_frame.grid_columnconfigure(2, weight=1)

        # Frame 3 Kartu
        self.card_rle = ctk.CTkFrame(self.cards_frame, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_rle.grid(row=0, column=0, padx=5, sticky="nsew")
        self.lbl_rle_summary = ctk.CTkLabel(self.card_rle, text="RLE\n\nAvg Saving: -\nAvg Time: -", font=("Segoe UI", 13, "bold"), justify="left")
        self.lbl_rle_summary.pack(padx=20, pady=15)

        self.card_lzw = ctk.CTkFrame(self.cards_frame, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_lzw.grid(row=0, column=1, padx=5, sticky="nsew")
        self.lbl_lzw_summary = ctk.CTkLabel(self.card_lzw, text="LZW\n\nAvg Saving: -\nAvg Time: -", font=("Segoe UI", 13, "bold"), justify="left")
        self.lbl_lzw_summary.pack(padx=20, pady=15)

        self.card_huf = ctk.CTkFrame(self.cards_frame, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_huf.grid(row=0, column=2, padx=5, sticky="nsew")
        self.lbl_huf_summary = ctk.CTkLabel(self.card_huf, text="Huffman\n\nAvg Saving: -\nAvg Time: -", font=("Segoe UI", 13, "bold"), justify="left")
        self.lbl_huf_summary.pack(padx=20, pady=15)

        # Panel Filter & Cari
        filter_section = ctk.CTkFrame(tab, fg_color="transparent")
        filter_section.grid(row=3, column=0, pady=(10, 5), sticky="ew")

        # Pencarian Nama File
        self.batch_search_var = ctk.StringVar()
        self.batch_search_var.trace_add("write", lambda *args: self.update_batch_table())
        search_lbl = ctk.CTkLabel(filter_section, text="🔍 Cari Gambar:", font=("Segoe UI", 12, "bold"))
        search_lbl.pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(
            filter_section, 
            width=250, 
            placeholder_text="Ketik nama gambar (contoh: img1)...",
            textvariable=self.batch_search_var,
            font=("Segoe UI", 12)
        )
        self.search_entry.pack(side="left", padx=5)

        # Filter Algoritma
        self.batch_filter_var = ctk.StringVar(value="Semua")
        filter_lbl = ctk.CTkLabel(filter_section, text="Filter Algoritma:", font=("Segoe UI", 12, "bold"))
        filter_lbl.pack(side="left", padx=(20, 5))
        self.filter_option = ctk.CTkOptionMenu(
            filter_section,
            values=["Semua", "RLE", "LZW", "Huffman"],
            variable=self.batch_filter_var,
            font=("Segoe UI", 12),
            command=lambda *args: self.update_batch_table()
        )
        self.filter_option.pack(side="left", padx=5)

        # Tabel Scrollable
        self.batch_scroll_frame = ctk.CTkScrollableFrame(tab, fg_color=("#f1f5f9", "#16161a"), corner_radius=10)
        self.batch_scroll_frame.grid(row=4, column=0, pady=(5, 0), sticky="nsew")

        # Populate awal jika file CSV ada
        if self.batch_df is not None:
            self.update_batch_summaries()
            self.update_batch_table()
            self.batch_status_lbl.configure(text="Data dimuat dari hasil_kompresi.csv.")

    def setup_tab_charts(self):
        tab = self.tabview.tab("Visualisasi Grafik")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Kontrol Atas
        self.charts_control_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.charts_control_frame.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        lbl_source = ctk.CTkLabel(self.charts_control_frame, text="Pilih Sumber Data Grafik:", font=("Segoe UI", 12, "bold"))
        lbl_source.pack(side="left", padx=10)

        self.chart_source_var = ctk.StringVar(value="Gambar Tunggal")
        self.chart_source_option = ctk.CTkOptionMenu(
            self.charts_control_frame,
            values=["Gambar Tunggal", "Analisis Dataset (Rata-rata)"],
            variable=self.chart_source_var,
            font=("Segoe UI", 12),
            command=lambda *args: self.draw_charts()
        )
        self.chart_source_option.pack(side="left", padx=5)

        self.btn_refresh_charts = ctk.CTkButton(
            self.charts_control_frame,
            text="🔄 Segarkan Grafik",
            font=("Segoe UI", 12, "bold"),
            fg_color=("#64748b", "#334155"),
            hover_color=("#475569", "#1e293b"),
            command=self.draw_charts
        )
        self.btn_refresh_charts.pack(side="left", padx=10)

        # Frame untuk Canvas Grafik
        self.chart_display_frame = ctk.CTkFrame(tab, fg_color=("#f1f5f9", "#16161a"), corner_radius=10)
        self.chart_display_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.draw_charts()

    def draw_charts(self):
        # Clear existing widgets in chart_display_frame
        for widget in self.chart_display_frame.winfo_children():
            widget.destroy()

        source = self.chart_source_var.get()
        appearance_mode = ctk.get_appearance_mode().lower() # 'dark' or 'light'
        
        # Colors based on theme
        if appearance_mode == "dark":
            bg_color = "#16161a"
            text_color = "#f8fafc"
            ax_bg = "#1e1e24"
            grid_color = "#334155"
        else:
            bg_color = "#f1f5f9"
            text_color = "#1e293b"
            ax_bg = "#ffffff"
            grid_color = "#cbd5e1"

        algos = ["RLE", "LZW", "Huffman"]
        bar_colors = ["#3b82f6", "#10b981", "#8b5cf6"] # Blue, Emerald, Violet

        ratios = []
        reductions = []
        times = []
        title_text = ""

        if source == "Gambar Tunggal":
            if not self.single_results:
                lbl = ctk.CTkLabel(
                    self.chart_display_frame,
                    text="Belum ada data Gambar Tunggal.\nSilakan pilih gambar dan klik 'Jalankan Kompresi' di tab pertama.",
                    font=("Segoe UI", 14, "bold"),
                    text_color=("#64748b", "#94a3b8")
                )
                lbl.pack(expand=True, pady=100)
                return
            
            for algo in algos:
                res = self.single_results[algo]
                ratio = res['orig_size'] / res['comp_size'] if res['comp_size'] > 0 else 1.0
                ratios.append(ratio)
                reductions.append(res['saving'])
                times.append(res['comp_time'])
            
            filename = os.path.basename(self.file_path) if self.file_path else "Gambar"
            title_text = f"Perbandingan Metrik Kompresi untuk: {filename}"

        else: # Analisis Dataset
            if self.batch_df is None or self.batch_df.empty:
                lbl = ctk.CTkLabel(
                    self.chart_display_frame,
                    text="Belum ada data Analisis Dataset.\nSilakan jalankan pengujian dataset di tab 'Analisis Dataset' terlebih dahulu.",
                    font=("Segoe UI", 14, "bold"),
                    text_color=("#64748b", "#94a3b8")
                )
                lbl.pack(expand=True, pady=100)
                return
            
            # Calculate averages
            avg_savings = self.batch_df.groupby("Algoritma")["Persentase"].mean()
            avg_times = self.batch_df.groupby("Algoritma")["Waktu_Kompresi"].mean()
            
            # Calculate average ratio
            if "Rasio" not in self.batch_df.columns:
                self.batch_df["Rasio"] = self.batch_df["Awal"] / self.batch_df["Akhir"]
            avg_ratios = self.batch_df.groupby("Algoritma")["Rasio"].mean()

            for algo in algos:
                ratios.append(avg_ratios.get(algo, 1.0))
                reductions.append(avg_savings.get(algo, 0.0))
                times.append(avg_times.get(algo, 0.0))
            
            num_images = len(self.batch_df) // 3
            title_text = f"Rata-rata Performa Kompresi pada Dataset ({num_images} Gambar)"

        # Create Matplotlib Figure
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(11, 4.5), facecolor=bg_color)
        fig.suptitle(title_text, color=text_color, fontsize=14, fontweight="bold", y=0.98)

        def style_ax(ax, title, ylabel):
            ax.set_title(title, color=text_color, fontsize=11, fontweight="bold", pad=10)
            ax.set_facecolor(ax_bg)
            ax.tick_params(colors=text_color, labelsize=9)
            ax.spines['bottom'].set_color(grid_color)
            ax.spines['top'].set_color('none')
            ax.spines['right'].set_color('none')
            ax.spines['left'].set_color(grid_color)
            ax.yaxis.grid(True, linestyle='--', alpha=0.5, color=grid_color)
            ax.set_ylabel(ylabel, color=text_color, fontsize=9)

        # Plot 1: Rasio Kompresi
        bars1 = ax1.bar(algos, ratios, color=bar_colors, width=0.5, edgecolor=bg_color, linewidth=1.5)
        style_ax(ax1, "Rasio Kompresi\n(lebih tinggi = lebih baik)", "Rasio (X : 1)")
        for bar in bars1:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.05, f"{yval:.2f}x", ha='center', va='bottom', color=text_color, fontsize=9, fontweight='bold')

        # Plot 2: Persentase Reduksi
        bars2 = ax2.bar(algos, reductions, color=bar_colors, width=0.5, edgecolor=bg_color, linewidth=1.5)
        style_ax(ax2, "Persentase Reduksi (%)\n(lebih tinggi = lebih baik)", "Persentase (%)")
        for bar in bars2:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f"{yval:.2f}%", ha='center', va='bottom', color=text_color, fontsize=9, fontweight='bold')

        # Plot 3: Waktu Proses Kompresi
        bars3 = ax3.bar(algos, times, color=bar_colors, width=0.5, edgecolor=bg_color, linewidth=1.5)
        style_ax(ax3, "Waktu Kompresi\n(lebih rendah = lebih cepat)", "Waktu (ms)")
        for bar in bars3:
            yval = bar.get_height()
            offset = 0.05 * max(times) if times and max(times) > 0 else 0.05
            ax3.text(bar.get_x() + bar.get_width()/2, yval + offset, f"{yval:.1f} ms", ha='center', va='bottom', color=text_color, fontsize=9, fontweight='bold')

        fig.tight_layout(rect=[0, 0.03, 1, 0.95])

        canvas = FigureCanvasTkAgg(fig, master=self.chart_display_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        plt.close(fig)

    def open_image(self):
        file_path = filedialog.askopenfilename(
            initialdir="bmp_dataset",
            filetypes=[("BMP Image", "*.bmp")]
        )

        if not file_path:
            return

        self.file_path = file_path
        self.single_results = None  # Reset hasil sebelumnya

        # Load dan tampilkan gambar asli
        self.display_preview(self.lbl_orig_preview, file_path)

        # Dapatkan detail gambar
        details = get_image_details(file_path)
        if details:
            self.lbl_orig_info.configure(text=f"{details['width']} x {details['height']} | {details['size']/1024:.2f} KB | {details['mode']}")
            
            # Update teks info sidebar
            detail_text = f"File: {os.path.basename(file_path)}\n"
            detail_text += f"Dimensi: {details['width']} x {details['height']}\n"
            detail_text += f"Format: BMP ({details['mode']})\n"
            detail_text += f"Ukuran: {details['size']/1024:.2f} KB\n"
            self.lbl_details_text.configure(text=detail_text, text_color=("#1e293b", "#f8fafc"))
        else:
            self.lbl_orig_info.configure(text="Gagal membaca metadata")
            self.lbl_details_text.configure(text="Error membaca info file.", text_color="#f43f5e")

        # Reset preview hasil dekompresi & tabel perbandingan
        for algo in ["huf", "lzw", "rle"]:
            getattr(self, f"lbl_{algo}_preview").configure(image=None, text="Menunggu kompresi...")
            getattr(self, f"lbl_{algo}_hex").configure(text="Menunggu kompresi...")
            getattr(self, f"lbl_{algo}_info").configure(text="-")
        self.build_comparison_table()
        if hasattr(self, "draw_charts"):
            self.draw_charts()

        # Aktifkan tombol kompresi
        self.btn_compress.configure(state="normal")

    def display_preview(self, label, path, max_size=200):
        try:
            img = Image.open(path)
            # Resize dengan rasio aspek tetap
            w, h = img.size
            if w > h:
                new_w = max_size
                new_h = int(h * (max_size / w))
            else:
                new_h = max_size
                new_w = int(w * (max_size / h))
                
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(new_w, new_h))
            label.configure(image=ctk_img, text="")
            label.image = ctk_img
        except Exception as e:
            label.configure(image=None, text=f"Error: {e}")

    def compress_image(self):
        if not self.file_path or not os.path.exists(self.file_path):
            messagebox.showwarning("Peringatan", "Silakan pilih gambar terlebih dahulu.")
            return

        self.btn_compress.configure(state="disabled")
        self.btn_open.configure(state="disabled")
        self.sidebar.update()

        filename = os.path.splitext(os.path.basename(self.file_path))[0]
        self.single_results = {}

        # Pastikan folder penyimpanan ada
        os.makedirs("compressed", exist_ok=True)
        os.makedirs("decompressed", exist_ok=True)

        algorithms = {
            "RLE": (rle_compress, rle_decompress),
            "LZW": (lzw_compress, lzw_decompress),
            "Huffman": (huffman_compress, huffman_decompress)
        }

        for algo_name, (comp_func, decomp_func) in algorithms.items():
            comp_file = os.path.join("compressed", f"{filename}_{algo_name}.bin")
            decomp_file = os.path.join("decompressed", f"{filename}_{algo_name}.bmp")

            # Ukur waktu kompresi
            t0 = time.perf_counter()
            comp_func(self.file_path, comp_file)
            t1 = time.perf_counter()
            comp_time = (t1 - t0) * 1000  # ms

            # Ukur waktu dekompresi
            t2 = time.perf_counter()
            decomp_func(comp_file, decomp_file)
            t3 = time.perf_counter()
            dec_time = (t3 - t2) * 1000  # ms

            # Metrik
            orig_size = os.path.getsize(self.file_path)
            comp_size = os.path.getsize(comp_file)
            saving = ((orig_size - comp_size) / orig_size) * 100

            # Validasi Lossless (Cek apakah byte identik)
            is_lossless = False
            if os.path.exists(decomp_file):
                try:
                    with open(self.file_path, "rb") as f1, open(decomp_file, "rb") as f2:
                        is_lossless = (f1.read() == f2.read())
                except Exception:
                    is_lossless = False

            metrics = calculate_metrics(self.file_path, decomp_file)

            self.single_results[algo_name] = {
                "orig_size": orig_size,
                "comp_size": comp_size,
                "comp_time": comp_time,
                "dec_time": dec_time,
                "saving": saving,
                "lossless": is_lossless,
                "decomp_path": decomp_file,
                "mse": metrics["mse"],
                "psnr": metrics["psnr"]
            }

        # Cari algoritma terbaik (persentase space saving tertinggi)
        best_algo = max(self.single_results.keys(), key=lambda k: self.single_results[k]["saving"])

        # Isi data tabel perbandingan
        for algo in ["RLE", "LZW", "Huffman"]:
            res = self.single_results[algo]
            
            self.table_cells[algo]["original"].configure(text=f"{res['orig_size']/1024:.2f} KB")
            self.table_cells[algo]["compressed"].configure(text=f"{res['comp_size']/1024:.2f} KB")
            
            ratio = res['orig_size'] / res['comp_size'] if res['comp_size'] > 0 else 1.0
            self.table_cells[algo]["ratio"].configure(text=f"{ratio:.2f} : 1")
            
            saving = res['saving']
            saving_text = f"{saving:.2f}%"
            saving_color = ("#10b981", "#10b981") if saving > 0 else (("#f43f5e", "#f43f5e") if saving < 0 else ("#1e293b", "#f8fafc"))
            self.table_cells[algo]["saving"].configure(text=saving_text, text_color=saving_color)
            
            self.table_cells[algo]["comp_time"].configure(text=f"{res['comp_time']:.2f} ms")
            self.table_cells[algo]["dec_time"].configure(text=f"{res['dec_time']:.2f} ms")
            
            valid_text = "✓ Cocok" if res['lossless'] else "✗ Berbeda"
            valid_color = ("#10b981", "#10b981") if res['lossless'] else (("#f43f5e", "#f43f5e"))
            self.table_cells[algo]["validation"].configure(text=valid_text, text_color=valid_color)
            
            # MSE & PSNR
            mse_val = res.get("mse")
            psnr_val = res.get("psnr")
            mse_text = f"{mse_val:.4f}" if mse_val is not None else "-"
            psnr_text = "∞" if psnr_val == float('inf') else (f"{psnr_val:.2f}" if psnr_val is not None else "-")
            
            self.table_cells[algo]["mse"].configure(text=mse_text)
            self.table_cells[algo]["psnr"].configure(text=psnr_text)

            if algo == best_algo:
                self.table_cells[algo]["status"].configure(text="🏆 Terbaik", text_color=("#10b981", "#10b981"))
            else:
                self.table_cells[algo]["status"].configure(text="-", text_color=("#64748b", "#94a3b8"))

        # Update preview hasil dekompresi & sorotan baris
        self.update_single_previews()
        if hasattr(self, "draw_charts"):
            self.draw_charts()

        self.btn_compress.configure(state="normal")
        self.btn_open.configure(state="normal")

    def update_single_previews(self):
        if not self.single_results:
            return

        # Tampilkan gambar hasil dekompresi dan metrik untuk ketiga algoritma
        filename = os.path.splitext(os.path.basename(self.file_path))[0]
        for algo in ["Huffman", "LZW", "RLE"]:
            res = self.single_results[algo]
            prefix = "huf" if algo == "Huffman" else algo.lower()
            
            lbl_preview = getattr(self, f"lbl_{prefix}_preview")
            lbl_hex = getattr(self, f"lbl_{prefix}_hex")
            lbl_info = getattr(self, f"lbl_{prefix}_info")
            
            # Display decompressed thumbnail
            self.display_preview(lbl_preview, res["decomp_path"], max_size=90)
            
            # Display compressed binary hex dump
            comp_file = os.path.join("compressed", f"{filename}_{algo}.bin")
            hex_dump = get_hex_dump(comp_file)
            lbl_hex.configure(text=hex_dump)
            
            # Tampilkan metrik MSE & PSNR di label info preview
            mse_val = res.get("mse")
            psnr_val = res.get("psnr")
            mse_text = f"{mse_val:.4f}" if mse_val is not None else "-"
            psnr_text = "Sempurna (∞)" if psnr_val == float('inf') else (f"{psnr_val:.2f} dB" if psnr_val is not None else "-")
            
            ratio = res['orig_size'] / res['comp_size'] if res['comp_size'] > 0 else 1.0
            info_text = (
                f"Ukuran Akhir: {res['comp_size']/1024:.2f} KB\n"
                f"Rasio Kompresi: {ratio:.2f} : 1\n"
                f"Persentase Reduksi: {res['saving']:.2f}%\n"
                f"Waktu Kompresi: {res['comp_time']:.2f} ms\n"
                f"Waktu Dekompresi: {res['dec_time']:.2f} ms\n"
                f"MSE: {mse_text} | PSNR: {psnr_text}"
            )
            lbl_info.configure(text=info_text)

        # Cari algoritma terbaik untuk highlight di tabel perbandingan
        best_algo = max(self.single_results.keys(), key=lambda k: self.single_results[k]["saving"])

        # Berikan sorotan (highlight) pada baris tabel algoritma terbaik
        for algo in ["RLE", "LZW", "Huffman"]:
            is_best = (algo == best_algo)
            bg_color = ("#d1fae5", "#064e3b") if is_best else ("#e2e8f0", "#16161a")
            
            for cell_key in ["name", "original", "compressed", "ratio", "saving", "comp_time", "dec_time", "validation", "mse", "psnr", "status"]:
                self.table_cells[algo][cell_key].configure(fg_color=bg_color)

    def switch_to_batch_tab(self):
        # Berpindah ke tab Analisis Dataset secara langsung
        self.tabview.set("Analisis Dataset")

    def run_batch_test(self):
        dataset_dir = "bmp_dataset"
        if not os.path.exists(dataset_dir):
            messagebox.showerror("Error", f"Folder '{dataset_dir}' tidak ditemukan!")
            return
            
        files = [f for f in os.listdir(dataset_dir) if f.endswith(".bmp")]
        if not files:
            messagebox.showerror("Error", f"Tidak ada file BMP di folder '{dataset_dir}'!")
            return
            
        total_files = len(files)
        total_tests = total_files * 3
        current_test = 0
        
        self.btn_run_batch.configure(state="disabled")
        self.batch_progress.set(0.0)
        
        results = []
        
        # Pastikan direktori penyimpanan ada
        os.makedirs("compressed", exist_ok=True)
        os.makedirs("decompressed", exist_ok=True)

        algorithms = {
            "RLE": (rle_compress, rle_decompress),
            "LZW": (lzw_compress, lzw_decompress),
            "Huffman": (huffman_compress, huffman_decompress)
        }

        # Loop pengujian massal
        for file_idx, filename in enumerate(files):
            img_path = os.path.join(dataset_dir, filename)
            
            for algo, (comp_func, decomp_func) in algorithms.items():
                self.batch_status_lbl.configure(text=f"Memproses {filename} ({algo})...")
                self.update()  # Jaga GUI tetap responsif
                
                comp_file = os.path.join("compressed", f"{os.path.splitext(filename)[0]}_{algo}.bin")
                decomp_file = os.path.join("decompressed", f"{os.path.splitext(filename)[0]}_{algo}.bmp")
                
                # Kompresi & Waktu
                t0 = time.perf_counter()
                comp_func(img_path, comp_file)
                t1 = time.perf_counter()
                comp_time = (t1 - t0) * 1000  # ms
                
                # Dekompresi & Waktu
                t2 = time.perf_counter()
                decomp_func(comp_file, decomp_file)
                t3 = time.perf_counter()
                dec_time = (t3 - t2) * 1000  # ms
                
                # Metrik
                actual_before = os.path.getsize(img_path)
                actual_after = os.path.getsize(comp_file)
                percent = ((actual_before - actual_after) / actual_before) * 100
                
                metrics = calculate_metrics(img_path, decomp_file)
                
                results.append({
                    "Gambar": filename,
                    "Algoritma": algo,
                    "Awal": actual_before,
                    "Akhir": actual_after,
                    "Persentase": percent,
                    "Waktu_Kompresi": comp_time,
                    "Waktu_Dekompresi": dec_time,
                    "MSE": metrics["mse"],
                    "PSNR": metrics["psnr"]
                })
                
                current_test += 1
                self.batch_progress.set(current_test / total_tests)
                self.update()
        
        # Simpan DataFrame ke CSV
        self.batch_df = pd.DataFrame(results)
        self.batch_df.to_csv("hasil_kompresi.csv", index=False)
        
        self.batch_status_lbl.configure(text="Pengujian selesai! Data disimpan ke hasil_kompresi.csv.")
        self.btn_run_batch.configure(state="normal")
        
        # Perbarui ringkasan & tabel scrollable
        self.update_batch_summaries()
        self.update_batch_table()
        if hasattr(self, "draw_charts"):
            self.draw_charts()
        
        messagebox.showinfo("Selesai", f"Pengujian selesai! Berhasil memproses {total_tests} pengujian.")

    def update_batch_summaries(self):
        if self.batch_df is None or self.batch_df.empty:
            self.lbl_rle_summary.configure(text="RLE\n\nRata-rata Reduksi: -\nRata-rata Waktu: -")
            self.lbl_lzw_summary.configure(text="LZW\n\nRata-rata Reduksi: -\nRata-rata Waktu: -")
            self.lbl_huf_summary.configure(text="Huffman\n\nRata-rata Reduksi: -\nRata-rata Waktu: -")
            return
            
        avg_savings = self.batch_df.groupby("Algoritma")["Persentase"].mean()
        avg_times = self.batch_df.groupby("Algoritma")["Waktu_Kompresi"].mean()
        
        best_algo = avg_savings.idxmax() if not avg_savings.empty else None
        
        for algo, card, lbl in [("RLE", self.card_rle, self.lbl_rle_summary), 
                                ("LZW", self.card_lzw, self.lbl_lzw_summary), 
                                ("Huffman", self.card_huf, self.lbl_huf_summary)]:
            saving = avg_savings.get(algo, 0.0)
            t_comp = avg_times.get(algo, 0.0)
            
            info_text = f"{algo}\n\n"
            info_text += f"Rata-rata Reduksi : {saving:.2f}%\n"
            info_text += f"Rata-rata Waktu   : {t_comp:.2f} ms\n"
            
            if algo == best_algo:
                info_text += "\n🏆 TERBAIK (REDUKSI TERTINGGI)"
                card.configure(border_color="#10b981", border_width=2)
            else:
                card.configure(border_color="#22222a", border_width=0)
                
            lbl.configure(text=info_text)

    def update_batch_table(self):
        # Bersihkan widget yang ada di dalam frame scroll
        for widget in self.batch_scroll_frame.winfo_children():
            widget.destroy()
            
        if self.batch_df is None or self.batch_df.empty:
            lbl = ctk.CTkLabel(
                self.batch_scroll_frame, 
                text="Belum ada data pengujian. Silakan klik tombol 'Jalankan 90 Pengujian' di atas.", 
                font=("Segoe UI", 13)
            )
            lbl.pack(pady=40)
            return

        # Saring data berdasarkan input filter dan cari
        df = self.batch_df.copy()
        
        algo = self.batch_filter_var.get()
        if algo != "Semua":
            df = df[df["Algoritma"] == algo]
            
        search = self.batch_search_var.get().strip().lower()
        if search:
            df = df[df["Gambar"].str.lower().str.contains(search)]

        if df.empty:
            lbl = ctk.CTkLabel(
                self.batch_scroll_frame, 
                text="Tidak ada data gambar yang cocok.", 
                font=("Segoe UI", 13)
            )
            lbl.pack(pady=40)
            return

        # Setup kolom grid di scroll frame
        for c in range(10):
            self.batch_scroll_frame.grid_columnconfigure(c, weight=1)

        # Header Tabel Scroll
        headers = ["No", "Nama Gambar", "Algoritma", "Ukuran Awal", "Ukuran Akhir", "Rasio Kompresi", "Persentase Reduksi (%)", "Waktu Kompresi (ms)", "MSE", "PSNR"]
        for col_idx, h in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.batch_scroll_frame, 
                text=h, 
                font=("Segoe UI", 11, "bold"), 
                text_color=("#475569", "#a0a0a5")
            )
            lbl.grid(row=0, column=col_idx, padx=5, pady=5, sticky="nsew")

        # Baris Data
        for i, (_, row) in enumerate(df.iterrows(), start=1):
            bg_color = ("#f1f5f9", "#1e1e24") if i % 2 == 0 else ("#e2e8f0", "#16161a")
            
            no_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=str(i), fg_color=bg_color, font=("Consolas", 12))
            no_lbl.grid(row=i, column=0, padx=1, pady=1, sticky="nsew")
            
            name_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=row["Gambar"], fg_color=bg_color, font=("Segoe UI", 12), anchor="w")
            name_lbl.grid(row=i, column=1, padx=5, pady=1, sticky="nsew")
            
            algo_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=row["Algoritma"], fg_color=bg_color, font=("Segoe UI", 12, "bold"))
            algo_lbl.grid(row=i, column=2, padx=1, pady=1, sticky="nsew")
            
            size_orig = row["Awal"]
            size_comp = row["Akhir"]
            
            orig_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=f"{size_orig/1024:.1f} KB", fg_color=bg_color, font=("Consolas", 12))
            orig_lbl.grid(row=i, column=3, padx=1, pady=1, sticky="nsew")
            
            comp_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=f"{size_comp/1024:.1f} KB", fg_color=bg_color, font=("Consolas", 12))
            comp_lbl.grid(row=i, column=4, padx=1, pady=1, sticky="nsew")
            
            ratio = size_orig / size_comp if size_comp > 0 else 1.0
            ratio_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=f"{ratio:.2f} : 1", fg_color=bg_color, font=("Consolas", 12))
            ratio_lbl.grid(row=i, column=5, padx=1, pady=1, sticky="nsew")
            
            saving = row["Persentase"]
            saving_color = ("#10b981", "#10b981") if saving > 0 else (("#f43f5e", "#f43f5e") if saving < 0 else ("#1e293b", "#f8fafc"))
            saving_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=f"{saving:.2f}%", fg_color=bg_color, text_color=saving_color, font=("Consolas", 12, "bold"))
            saving_lbl.grid(row=i, column=6, padx=1, pady=1, sticky="nsew")
            
            time_comp = row.get("Waktu_Kompresi", 0.0)
            time_str = f"{time_comp:.1f} ms" if time_comp > 0 else "N/A"
            time_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=time_str, fg_color=bg_color, font=("Consolas", 12))
            time_lbl.grid(row=i, column=7, padx=1, pady=1, sticky="nsew")

            mse_val = row.get("MSE")
            psnr_val = row.get("PSNR")
            mse_str = f"{mse_val:.4f}" if pd.notna(mse_val) else "-"
            psnr_str = "∞" if (psnr_val == float('inf') or (pd.notna(psnr_val) and str(psnr_val).lower() == 'inf')) else (f"{psnr_val:.2f}" if pd.notna(psnr_val) else "-")
            
            mse_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=mse_str, fg_color=bg_color, font=("Consolas", 12))
            mse_lbl.grid(row=i, column=8, padx=1, pady=1, sticky="nsew")
            
            psnr_lbl = ctk.CTkLabel(self.batch_scroll_frame, text=psnr_str, fg_color=bg_color, font=("Consolas", 12))
            psnr_lbl.grid(row=i, column=9, padx=1, pady=1, sticky="nsew")

    def toggle_theme(self):
        theme = self.switch_theme_var.get()
        if theme == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        if hasattr(self, "draw_charts"):
            self.draw_charts()

# Bootstrapping
if __name__ == "__main__":
    app = App()
    app.mainloop()