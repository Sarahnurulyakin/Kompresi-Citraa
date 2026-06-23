import os
import re
import pandas as pd
import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ================= NATURAL SORT =================
def natural_key(text):
    digits = re.findall(r'\d+', text)
    return int(digits[0]) if digits else 999


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

        # ================= PERFORMANCE CHART =================
        self.chart_display_frame = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#1e1e24"), corner_radius=10)
        self.chart_display_frame.pack(fill="x", padx=20, pady=10)
        self.show_chart()

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
            info += f"Rata-rata Reduksi : {saving:.2f}%\n"
            info += f"Rata-rata Waktu   : {time_comp:.2f} ms"
            
            if algo == best:
                info += "\n\n🏆 TERBAIK (REDUKSI TERTINGGI)"
                card.configure(border_color="#10b981", border_width=2)

            lbl = ctk.CTkLabel(card, text=info, font=("Segoe UI", 13, "bold"), justify="left")
            lbl.pack(padx=20, pady=15)

    def show_chart(self):
        # Clear existing widgets
        for widget in self.chart_display_frame.winfo_children():
            widget.destroy()

        if self.df is None or self.df.empty:
            lbl = ctk.CTkLabel(
                self.chart_display_frame,
                text="Belum ada data untuk grafik. Silakan jalankan pengujian dari aplikasi utama.",
                font=("Segoe UI", 12, "bold")
            )
            lbl.pack(pady=20)
            return

        appearance_mode = ctk.get_appearance_mode().lower() # 'dark' or 'light'
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

        # Averages
        avg_savings = self.df.groupby("Algoritma")["Persentase"].mean()
        avg_times = self.df.groupby("Algoritma")["Waktu_Kompresi"].mean()
        
        if "Rasio" not in self.df.columns:
            self.df["Rasio"] = self.df["Awal"] / self.df["Akhir"]
        avg_ratios = self.df.groupby("Algoritma")["Rasio"].mean()

        ratios = [avg_ratios.get(algo, 1.0) for algo in algos]
        reductions = [avg_savings.get(algo, 0.0) for algo in algos]
        times = [avg_times.get(algo, 0.0) for algo in algos]

        # Create Matplotlib Figure
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 2.6), facecolor=bg_color)

        def style_ax(ax, title, ylabel):
            ax.set_title(title, color=text_color, fontsize=10, fontweight="bold", pad=5)
            ax.set_facecolor(ax_bg)
            ax.tick_params(colors=text_color, labelsize=8)
            ax.spines['bottom'].set_color(grid_color)
            ax.spines['top'].set_color('none')
            ax.spines['right'].set_color('none')
            ax.spines['left'].set_color(grid_color)
            ax.yaxis.grid(True, linestyle='--', alpha=0.5, color=grid_color)
            ax.set_ylabel(ylabel, color=text_color, fontsize=8)

        # Plot 1: Average Rasio
        bars1 = ax1.bar(algos, ratios, color=bar_colors, width=0.45, edgecolor=bg_color, linewidth=1)
        style_ax(ax1, "Rata-rata Rasio Kompresi", "Rasio (X:1)")
        for bar in bars1:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f"{yval:.2f}x", ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')

        # Plot 2: Average Reduksi %
        bars2 = ax2.bar(algos, reductions, color=bar_colors, width=0.45, edgecolor=bg_color, linewidth=1)
        style_ax(ax2, "Rata-rata Persentase Reduksi", "Reduksi (%)")
        for bar in bars2:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.3, f"{yval:.2f}%", ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')

        # Plot 3: Average Waktu
        bars3 = ax3.bar(algos, times, color=bar_colors, width=0.45, edgecolor=bg_color, linewidth=1)
        style_ax(ax3, "Rata-rata Waktu Kompresi", "Waktu (ms)")
        for bar in bars3:
            yval = bar.get_height()
            offset = 0.03 * max(times) if times and max(times) > 0 else 0.03
            ax3.text(bar.get_x() + bar.get_width()/2, yval + offset, f"{yval:.1f} ms", ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_display_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        plt.close(fig)

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

        # Panel Gambar (Grid 2x2)
        img_grid = ctk.CTkFrame(card, fg_color="transparent")
        img_grid.pack(pady=5, padx=10)
        img_grid.grid_columnconfigure(0, weight=1)
        img_grid.grid_columnconfigure(1, weight=1)
        img_grid.grid_rowconfigure(0, weight=1)
        img_grid.grid_rowconfigure(1, weight=1)

        img_path = os.path.join("bmp_dataset", img_name)
        max_size = 100

        def add_preview(row_num, col_num, title, path):
            # Container frame for image + label
            container = ctk.CTkFrame(img_grid, fg_color="transparent")
            container.grid(row=row_num, column=col_num, padx=4, pady=4)
            
            # Tiny title label
            lbl_title = ctk.CTkLabel(container, text=title, font=("Segoe UI", 10, "bold"), text_color=("#64748b", "#94a3b8"))
            lbl_title.pack(pady=(0, 2))

            img_loaded = False
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    img.thumbnail((max_size, max_size))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    lbl_img = ctk.CTkLabel(container, image=ctk_img, text="")
                    lbl_img.image = ctk_img
                    lbl_img.pack()
                    img_loaded = True
                except Exception:
                    pass

            if not img_loaded:
                lbl_err = ctk.CTkLabel(
                    container, 
                    text="N/A", 
                    width=max_size, 
                    height=max_size, 
                    fg_color=("#cbd5e1", "#16161a"), 
                    corner_radius=4,
                    font=("Segoe UI", 10)
                )
                lbl_err.pack()

        # Load 4 Preview (Original + 3 Decompressed)
        add_preview(0, 0, "Asli", img_path)
        add_preview(0, 1, "Huffman", os.path.join("decompressed", img_name.replace(".bmp", "_Huffman.bmp")))
        add_preview(1, 0, "LZW", os.path.join("decompressed", img_name.replace(".bmp", "_LZW.bmp")))
        add_preview(1, 1, "RLE", os.path.join("decompressed", img_name.replace(".bmp", "_RLE.bmp")))

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
                
                # Hitung MSE & PSNR secara dinamis
                decomp_file = os.path.join("decompressed", img_name.replace(".bmp", f"_{name}.bmp"))
                metrics = calculate_metrics(img_path, decomp_file)
                mse_val = metrics["mse"]
                psnr_val = metrics["psnr"]
                
                mse_text = f"{mse_val:.2f}" if mse_val is not None else "-"
                psnr_text = "Sempurna" if psnr_val == float('inf') else (f"{psnr_val:.1f}dB" if psnr_val is not None else "-")
                
                ratio = data_algo['awal'] / data_algo['akhir'] if data_algo['akhir'] > 0 else 1.0
                line = f"{name:<7}: {akhir_kb:5.1f} KB ({ratio:.2f}:1) | Reduksi: {persen:5.1f}% | {waktu:4.1f} ms | PSNR: {psnr_text}"
                if name == best_algo:
                    line += " ⭐"
                info_lines.append(line)

        orig_size_kb = rle.get('awal', 0)/1024 if rle else (lzw.get('awal', 0)/1024 if lzw else 0)
        info = "\n".join(info_lines)
        info += f"\n\nUkuran Asli: {orig_size_kb:.2f} KB"

        label = ctk.CTkLabel(
            card,
            text=info,
            justify="left",
            font=("Consolas", 10),
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