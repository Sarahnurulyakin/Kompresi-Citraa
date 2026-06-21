import os
import re
import pandas as pd
import customtkinter as ctk
from PIL import Image, ImageTk


# ================= NATURAL SORT =================
def natural_key(text):
    digits = re.findall(r'\d+', text)
    return int(digits[0]) if digits else 999


class Dashboard(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Dashboard Kompresi Citra - Presentasi Premium")
        self.geometry("1400x880")
        self.minsize(1024, 768)

        # Set default appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.df = None
        self.load_data()

        # ================= HEADER =================
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            self.header_frame,
            text="STUDI KOMPARASI ALGORITMA KOMPRESI CITRA",
            font=("Segoe UI", 24, "bold"),
            text_color=("#1e293b", "#f8fafc")
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            self.header_frame,
            text="Visualisasi Performa Dataset RLE vs LZW vs Huffman",
            font=("Segoe UI", 14, "italic"),
            text_color=("#64748b", "#94a3b8")
        )
        subtitle.pack(anchor="w", pady=(0, 10))

        # ================= SUMMARY CARDS =================
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=20, pady=5)
        self.show_summary()

        # ================= SEARCH & CONTROLS =================
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(fill="x", padx=20, pady=5)
        
        search_lbl = ctk.CTkLabel(self.control_frame, text="🔍 Cari Gambar:", font=("Segoe UI", 12, "bold"))
        search_lbl.pack(side="left", padx=5)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.render_grid())
        self.search_entry = ctk.CTkEntry(
            self.control_frame,
            width=300,
            placeholder_text="Ketik nama gambar (contoh: img1)...",
            textvariable=self.search_var,
            font=("Segoe UI", 12)
        )
        self.search_entry.pack(side="left", padx=5)

        # ================= SCROLL AREA =================
        self.wrapper = ctk.CTkScrollableFrame(self, fg_color=("#f1f5f9", "#121214"))
        self.wrapper.pack(fill="both", expand=True, padx=20, pady=15)

        # ================= RENDER GRID =================
        self.render_grid()

    def load_data(self):
        if os.path.exists("hasil_kompresi.csv"):
            try:
                self.df = pd.read_csv("hasil_kompresi.csv")
                # Pastikan kolom waktu ada
                if "Waktu_Kompresi" not in self.df.columns:
                    self.df["Waktu_Kompresi"] = 0.0
                if "Waktu_Dekompresi" not in self.df.columns:
                    self.df["Waktu_Dekompresi"] = 0.0
            except Exception as e:
                print(f"Error loading CSV in dashboard: {e}")

    def show_summary(self):
        # Bersihkan frame ringkasan
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        if self.df is None or self.df.empty:
            lbl = ctk.CTkLabel(
                self.summary_frame, 
                text="Belum ada data pengujian. Silakan jalankan pengujian dari aplikasi utama (app.py) terlebih dahulu.", 
                font=("Segoe UI", 13)
            )
            lbl.pack(pady=10)
            return

        avg = self.df.groupby("Algoritma")["Persentase"].mean()
        avg_times = self.df.groupby("Algoritma")["Waktu_Kompresi"].mean()
        best = avg.idxmax() if not avg.empty else None

        # Setup layout grid 3 kolom
        for c in range(3):
            self.summary_frame.grid_columnconfigure(c, weight=1)

        for idx, algo in enumerate(["RLE", "LZW", "Huffman"]):
            card = ctk.CTkFrame(self.summary_frame, fg_color=("#f8fafc", "#1e1e24"), corner_radius=10)
            card.grid(row=0, column=idx, padx=5, sticky="nsew")

            saving = avg.get(algo, 0.0)
            time_comp = avg_times.get(algo, 0.0)

            info = f"{algo}\n\n"
            info += f"Rata-rata Saving : {saving:.2f}%\n"
            info += f"Rata-rata Waktu  : {time_comp:.2f} ms"
            
            if algo == best:
                info += "\n\n🏆 ALGORITMA TERBAIK (RATA-RATA)"
                card.configure(border_color="#10b981", border_width=2)

            lbl = ctk.CTkLabel(card, text=info, font=("Segoe UI", 13, "bold"), justify="left")
            lbl.pack(padx=20, pady=15)

    def group_data(self):
        if self.df is None or self.df.empty:
            return {}

        data = {}
        for _, row in self.df.iterrows():
            img = row["Gambar"]
            if img not in data:
                data[img] = {}

            data[img][row["Algoritma"]] = {
                "awal": row["Awal"],
                "akhir": row["Akhir"],
                "persen": row["Persentase"],
                "waktu": row.get("Waktu_Kompresi", 0.0)
            }

        return data

    def create_card(self, parent, img_name, values):
        card = ctk.CTkFrame(parent, fg_color=("#e2e8f0", "#1e1e24"), corner_radius=15)
        card.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        img_index = natural_key(img_name)

        # Judul Kartu
        title_lbl = ctk.CTkLabel(
            card,
            text=f"Gambar {img_index} ({img_name})",
            font=("Segoe UI", 15, "bold"),
            text_color=("#1e293b", "#f8fafc")
        )
        title_lbl.pack(anchor="w", padx=15, pady=(10, 5))

        # Panel Gambar
        img_row = ctk.CTkFrame(card, fg_color="transparent")
        img_row.pack(pady=5)

        img_path = os.path.join("bmp_dataset", img_name)
        max_size = 140

        # Load Gambar Asli
        if os.path.exists(img_path):
            try:
                img_o = Image.open(img_path)
                img_o.thumbnail((max_size, max_size))
                ctk_img_o = ctk.CTkImage(light_image=img_o, dark_image=img_o, size=img_o.size)
                
                lbl_o = ctk.CTkLabel(img_row, image=ctk_img_o, text="")
                lbl_o.image = ctk_img_o
                lbl_o.pack(side="left", padx=5)
            except Exception:
                pass

        # Load Gambar Hasil Dekompresi (Gunakan LZW sebagai representasi lossless)
        lzw_decomp_path = os.path.join("decompressed", img_name.replace(".bmp", "_LZW.bmp"))
        res_path = lzw_decomp_path if os.path.exists(lzw_decomp_path) else img_path

        if os.path.exists(res_path):
            try:
                img_r = Image.open(res_path)
                img_r.thumbnail((max_size, max_size))
                ctk_img_r = ctk.CTkImage(light_image=img_r, dark_image=img_r, size=img_r.size)
                
                lbl_r = ctk.CTkLabel(img_row, image=ctk_img_r, text="")
                lbl_r.image = ctk_img_r
                lbl_r.pack(side="left", padx=5)
            except Exception:
                pass

        # Teks Metrik
        rle = values.get("RLE", {})
        huf = values.get("Huffman", {})
        lzw = values.get("LZW", {})

        # Cari algoritma terbaik untuk gambar ini
        avail_algos = []
        if rle: avail_algos.append(("RLE", rle.get("persen", -999.0)))
        if huf: avail_algos.append(("Huffman", huf.get("persen", -999.0)))
        if lzw: avail_algos.append(("LZW", lzw.get("persen", -999.0)))
        
        best_algo = max(avail_algos, key=lambda x: x[1])[0] if avail_algos else None

        info_lines = []
        for name, data_algo in [("RLE", rle), ("Huffman", huf), ("LZW", lzw)]:
            if data_algo:
                akhir_kb = data_algo['akhir']/1024
                persen = data_algo['persen']
                waktu = data_algo.get("waktu", 0.0)
                
                line = f"{name:<8}: {akhir_kb:7.2f} KB | {persen:6.2f}%"
                if waktu > 0:
                    line += f" | {waktu:5.1f} ms"
                if name == best_algo:
                    line += " ⭐️"
                info_lines.append(line)

        orig_size_kb = rle.get('awal', 0)/1024 if rle else (lzw.get('awal', 0)/1024 if lzw else 0)
        info = "\n".join(info_lines)
        info += f"\n\nUkuran Asli: {orig_size_kb:.2f} KB"

        label = ctk.CTkLabel(
            card,
            text=info,
            justify="left",
            font=("Consolas", 12),
            text_color=("#1e293b", "#e2e8f0")
        )
        label.pack(pady=10, padx=15, fill="x")

    def render_grid(self):
        # Bersihkan area scroll
        for widget in self.wrapper.winfo_children():
            widget.destroy()

        if self.df is None or self.df.empty:
            lbl = ctk.CTkLabel(
                self.wrapper, 
                text="Tidak ada data untuk ditampilkan. Pastikan hasil_kompresi.csv tersedia.", 
                font=("Segoe UI", 13)
            )
            lbl.pack(pady=40)
            return

        data = self.group_data()
        
        # Terapkan filter pencarian
        search_query = self.search_var.get().strip().lower()
        filtered_data = {}
        for img_name, values in data.items():
            if not search_query or search_query in img_name.lower():
                filtered_data[img_name] = values

        if not filtered_data:
            lbl = ctk.CTkLabel(
                self.wrapper, 
                text="Tidak ada gambar yang cocok dengan kata kunci.", 
                font=("Segoe UI", 13)
            )
            lbl.pack(pady=40)
            return

        # Urutkan gambar secara natural
        items = sorted(filtered_data.items(), key=lambda x: natural_key(x[0]))

        row = None
        for i, (img_name, values) in enumerate(items):
            if i % 3 == 0:
                row = ctk.CTkFrame(self.wrapper, fg_color="transparent")
                row.pack(fill="x", pady=5)

            self.create_card(row, img_name, values)


# ================= RUN =================
if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()