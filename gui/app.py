import os
import time
import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# Import compression/decompression functions
from algorithms.rle import compress_file as rle_compress
from algorithms.rle import decompress_file as rle_decompress
from algorithms.lzw import compress_file as lzw_compress
from algorithms.lzw import decompress_file as lzw_decompress
from algorithms.huffman import compress_file as huffman_compress
from algorithms.huffman import decompress_file as huffman_decompress


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

        # Setup Tab 1 & Tab 2
        self.setup_tab_single()
        self.setup_tab_batch()

    def setup_tab_single(self):
        tab = self.tabview.tab("Kompresi Tunggal")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=3)  # Preview Frame
        tab.grid_rowconfigure(1, weight=0)  # Segmented Button
        tab.grid_rowconfigure(2, weight=2)  # Comparison Table Frame

        # Frame Panel Preview (Original vs Decompressed)
        self.previews_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.previews_frame.grid(row=0, column=0, pady=(10, 10), sticky="nsew")
        self.previews_frame.grid_columnconfigure(0, weight=1)
        self.previews_frame.grid_columnconfigure(1, weight=1)
        self.previews_frame.grid_rowconfigure(0, weight=1)

        # Kartu Gambar Original
        self.card_orig = ctk.CTkFrame(self.previews_frame, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_orig.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        lbl_orig_title = ctk.CTkLabel(
            self.card_orig, 
            text="🖼️ GAMBAR ASLI (ORIGINAL)", 
            font=("Segoe UI", 13, "bold"), 
            text_color=("#1e293b", "#f8fafc")
        )
        lbl_orig_title.pack(pady=10)

        self.lbl_orig_preview = ctk.CTkLabel(
            self.card_orig, 
            text="Belum ada gambar yang dipilih", 
            width=320, 
            height=320, 
            fg_color=("#cbd5e1", "#16161a"), 
            corner_radius=8
        )
        self.lbl_orig_preview.pack(padx=15, pady=5, expand=True)

        self.lbl_orig_info = ctk.CTkLabel(self.card_orig, text="-", font=("Segoe UI", 12), text_color=("#64748b", "#94a3b8"))
        self.lbl_orig_info.pack(pady=(5, 10))

        # Kartu Gambar Decompressed
        self.card_decomp = ctk.CTkFrame(self.previews_frame, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.card_decomp.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        lbl_decomp_title = ctk.CTkLabel(
            self.card_decomp, 
            text="📥 HASIL DEKOMPRESI", 
            font=("Segoe UI", 13, "bold"), 
            text_color=("#1e293b", "#f8fafc")
        )
        lbl_decomp_title.pack(pady=10)

        self.lbl_decomp_preview = ctk.CTkLabel(
            self.card_decomp, 
            text="Silakan jalankan kompresi", 
            width=320, 
            height=320, 
            fg_color=("#cbd5e1", "#16161a"), 
            corner_radius=8
        )
        self.lbl_decomp_preview.pack(padx=15, pady=5, expand=True)

        self.lbl_decomp_info = ctk.CTkLabel(self.card_decomp, text="-", font=("Segoe UI", 12), text_color=("#64748b", "#94a3b8"))
        self.lbl_decomp_info.pack(pady=(5, 10))

        # Segmented Button (Selector Algoritma)
        self.segmented_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.segmented_frame.grid(row=1, column=0, pady=10, sticky="ew")
        
        lbl_select_algo = ctk.CTkLabel(self.segmented_frame, text="Pilih Algoritma Preview:", font=("Segoe UI", 13, "bold"))
        lbl_select_algo.pack(side="left", padx=10)

        self.active_algo_var = ctk.StringVar(value="LZW")
        self.active_algo_btn = ctk.CTkSegmentedButton(
            self.segmented_frame,
            values=["RLE", "LZW", "Huffman"],
            variable=self.active_algo_var,
            font=("Segoe UI", 12, "bold"),
            command=self.on_active_algo_changed
        )
        self.active_algo_btn.pack(side="left", padx=10)

        # Tabel Perbandingan (Bawah)
        self.table_wrapper = ctk.CTkFrame(tab, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.table_wrapper.grid(row=2, column=0, pady=(10, 0), sticky="nsew")
        
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
        for c in range(9):
            self.table_frame.grid_columnconfigure(c, weight=1)

        self.build_comparison_table()

    def build_comparison_table(self):
        # Hapus widget yang sudah ada
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        headers = [
            "Algoritma", "Ukuran Awal", "Ukuran Akhir", 
            "Rasio Kompresi", "Space Saving", "Waktu Kompresi", 
            "Waktu Dekompresi", "Validasi Lossless", "Status"
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

            self.table_cells[algo]["status"] = ctk.CTkLabel(self.table_frame, text="-", font=("Segoe UI", 12, "bold"), fg_color=bg_color)
            self.table_cells[algo]["status"].grid(row=row_idx, column=8, padx=1, pady=1, sticky="nsew")

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
        self.lbl_decomp_preview.configure(image=None, text="Menunggu kompresi...")
        self.lbl_decomp_info.configure(text="-")
        self.build_comparison_table()

        # Aktifkan tombol kompresi
        self.btn_compress.configure(state="normal")

    def display_preview(self, label, path):
        try:
            img = Image.open(path)
            # Resize dengan rasio aspek tetap
            max_size = 300
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

            self.single_results[algo_name] = {
                "orig_size": orig_size,
                "comp_size": comp_size,
                "comp_time": comp_time,
                "dec_time": dec_time,
                "saving": saving,
                "lossless": is_lossless,
                "decomp_path": decomp_file
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
            
            if algo == best_algo:
                self.table_cells[algo]["status"].configure(text="🏆 Terbaik", text_color=("#10b981", "#10b981"))
            else:
                self.table_cells[algo]["status"].configure(text="-", text_color=("#64748b", "#94a3b8"))

        # Update preview hasil dekompresi & sorotan baris
        self.update_single_previews()

        self.btn_compress.configure(state="normal")
        self.btn_open.configure(state="normal")

    def update_single_previews(self):
        if not self.single_results:
            return

        active_algo = self.active_algo_var.get()
        res = self.single_results[active_algo]

        # Tampilkan gambar hasil dekompresi
        self.display_preview(self.lbl_decomp_preview, res["decomp_path"])

        # Update label info hasil dekompresi
        ratio = res['orig_size'] / res['comp_size'] if res['comp_size'] > 0 else 1.0
        info_text = f"{res['comp_size']/1024:.2f} KB | Rasio: {ratio:.2f}:1 | Saving: {res['saving']:.2f}% | Kompresi: {res['comp_time']:.1f} ms"
        self.lbl_decomp_info.configure(text=info_text)

        # Berikan sorotan (highlight) pada baris tabel algoritma yang aktif
        for algo in ["RLE", "LZW", "Huffman"]:
            is_active = (algo == active_algo)
            bg_color = ("#d1d5db", "#2e2e38") if is_active else ("#e2e8f0", "#16161a")
            
            for cell_key in ["name", "original", "compressed", "ratio", "saving", "comp_time", "dec_time", "validation", "status"]:
                self.table_cells[algo][cell_key].configure(fg_color=bg_color)

    def on_active_algo_changed(self, value):
        self.update_single_previews()

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
                
                results.append({
                    "Gambar": filename,
                    "Algoritma": algo,
                    "Awal": actual_before,
                    "Akhir": actual_after,
                    "Persentase": percent,
                    "Waktu_Kompresi": comp_time,
                    "Waktu_Dekompresi": dec_time
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
        
        messagebox.showinfo("Selesai", f"Pengujian selesai! Berhasil memproses {total_tests} pengujian.")

    def update_batch_summaries(self):
        if self.batch_df is None or self.batch_df.empty:
            self.lbl_rle_summary.configure(text="RLE\n\nAvg Saving: -\nAvg Time: -")
            self.lbl_lzw_summary.configure(text="LZW\n\nAvg Saving: -\nAvg Time: -")
            self.lbl_huf_summary.configure(text="Huffman\n\nAvg Saving: -\nAvg Time: -")
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
            info_text += f"Rata-rata Saving : {saving:.2f}%\n"
            info_text += f"Rata-rata Waktu  : {t_comp:.2f} ms\n"
            
            if algo == best_algo:
                info_text += "\n🏆 TERBAIK (HIGHEST SAVING)"
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
        for c in range(8):
            self.batch_scroll_frame.grid_columnconfigure(c, weight=1)

        # Header Tabel Scroll
        headers = ["No", "Nama Gambar", "Algoritma", "Ukuran Awal", "Ukuran Akhir", "Rasio", "Space Saving", "Waktu Kompresi"]
        for col_idx, h in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.batch_scroll_frame, 
                text=h, 
                font=("Segoe UI", 12, "bold"), 
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

    def toggle_theme(self):
        theme = self.switch_theme_var.get()
        if theme == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

# Bootstrapping
if __name__ == "__main__":
    app = App()
    app.mainloop()