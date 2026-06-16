import os
import re
import pandas as pd
import customtkinter as ctk
from PIL import Image, ImageTk


# ================= NATURAL SORT =================
def natural_key(text):
    return int(re.findall(r'\d+', text)[0])


class Dashboard(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Dashboard Kompresi Citra - Presentasi")
        self.geometry("1400x850")

        ctk.set_appearance_mode("light")

        # ================= LOAD CSV =================
        self.df = pd.read_csv("hasil_kompresi.csv")

        # ================= HEADER =================
        title = ctk.CTkLabel(
            self,
            text="STUDI KOMPARASI ALGORITMA KOMPRESI CITRA\n(RLE vs LZW vs Huffman)",
            font=("Arial", 26, "bold")
        )
        title.pack(pady=10)

        # ================= SUMMARY =================
        self.show_summary()

        # ================= SCROLL AREA =================
        self.wrapper = ctk.CTkScrollableFrame(self)
        self.wrapper.pack(fill="both", expand=True, padx=10, pady=10)

        # ================= RENDER GRID =================
        self.render_grid()

    # ================= SUMMARY =================
    def show_summary(self):

        avg = self.df.groupby("Algoritma")["Persentase"].mean()
        best = avg.idxmax()

        text = "Rata-rata Kompresi:\n\n"

        for k, v in avg.items():
            if k == best:
                text += f"🏆 {k:<10}: {v:.2f}% (BEST)\n"
            else:
                text += f"{k:<10}: {v:.2f}%\n"

        label = ctk.CTkLabel(
            self,
            text=text,
            font=("Arial", 14),
            justify="left"
        )
        label.pack()

    # ================= GROUP DATA =================
    def group_data(self):

        data = {}

        for _, row in self.df.iterrows():

            img = row["Gambar"]

            if img not in data:
                data[img] = {}

            data[img][row["Algoritma"]] = {
                "awal": row["Awal"],
                "akhir": row["Akhir"],
                "persen": row["Persentase"]
            }

        return data

    # ================= CARD =================
    def create_card(self, parent, img_name, values):

        card = ctk.CTkFrame(parent, corner_radius=15)
        card.pack(fill="x", padx=10, pady=10)

        img_index = natural_key(img_name)

        # ================= TITLE =================
        title = ctk.CTkLabel(
            card,
            text=f"Gambar {img_index} ({img_name})",
            font=("Arial", 16, "bold")
        )
        title.pack(anchor="w", padx=10, pady=5)

        # ================= IMAGE ROW =================
        img_row = ctk.CTkFrame(card)
        img_row.pack(pady=5)

        # ===== BEFORE IMAGE =====
        img_path = os.path.join("bmp_dataset", img_name)

        img_before = None
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img.thumbnail((160, 160))
            img_before = ImageTk.PhotoImage(img)

            lbl1 = ctk.CTkLabel(img_row, image=img_before, text="ORIGINAL")
            lbl1.image = img_before
            lbl1.pack(side="left", padx=10)

        # ===== AFTER IMAGE (LOSSLESS RESULT / FALLBACK) =====
        after_path = os.path.join(
            "decompressed",
            img_name.replace(".bmp", "_LZW.bmp")
        )

        if os.path.exists(after_path):
            img2 = Image.open(after_path)
        else:
            # fallback karena lossless → sama dengan input
            img2 = Image.open(img_path)

        img2.thumbnail((160, 160))
        img_after = ImageTk.PhotoImage(img2)

        lbl2 = ctk.CTkLabel(img_row, image=img_after, text="RESULT")
        lbl2.image = img_after
        lbl2.pack(side="left", padx=10)

        # ================= INFO =================
        info = ""

        rle = values.get("RLE", {})
        huf = values.get("Huffman", {})
        lzw = values.get("LZW", {})

        if rle:
            info += f"RLE      : {rle['akhir']/1024:.2f} KB | {rle['persen']:.2f}%\n"

        if huf:
            info += f"Huffman  : {huf['akhir']/1024:.2f} KB | {huf['persen']:.2f}%\n"

        if lzw:
            info += f"LZW      : {lzw['akhir']/1024:.2f} KB | {lzw['persen']:.2f}%\n"

        # ukuran awal pakai salah satu (RLE)
        info += f"\nUkuran Awal: {rle.get('awal', 0)/1024:.2f} KB"

        label = ctk.CTkLabel(
            card,
            text=info,
            justify="left",
            font=("Arial", 13)
        )
        label.pack(pady=10)

    # ================= GRID =================
    def render_grid(self):

        data = self.group_data()

        # FIX URUTAN 1–30
        items = sorted(data.items(), key=lambda x: natural_key(x[0]))

        row = None

        for i, (img_name, values) in enumerate(items):

            if i % 3 == 0:
                row = ctk.CTkFrame(self.wrapper)
                row.pack(fill="x", pady=10)

            self.create_card(row, img_name, values)


# ================= RUN =================
if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()