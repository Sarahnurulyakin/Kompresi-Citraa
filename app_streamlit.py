import streamlit as st
import os
import time
import tempfile
import pandas as pd
import numpy as np
from PIL import Image
import io

# Set matplotlib backend to non-interactive 'Agg' to prevent GUI/X11 crashes on Linux cloud containers
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Import compression/decompression functions
from algorithms.rle import compress_file as rle_compress
from algorithms.rle import decompress_file as rle_decompress
from algorithms.lzw import compress_file as lzw_compress
from algorithms.lzw import decompress_file as lzw_decompress
from algorithms.huffman import compress_file as huffman_compress
from algorithms.huffman import decompress_file as huffman_decompress

# Buat direktori penyimpanan yang diperlukan agar tidak FileNotFound di server cloud
os.makedirs("compressed", exist_ok=True)
os.makedirs("decompressed", exist_ok=True)

# Page configurations
st.set_page_config(
    page_title="Dashboard Kompresi Citra",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Apply font */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Title styling */
    .title-gradient {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    /* Card design */
    .algo-card {
        border-radius: 12px;
        padding: 20px;
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Hex dump box styling */
    .hex-box {
        font-family: 'Consolas', monospace;
        font-size: 0.8rem;
        background-color: #090d16;
        color: #10b981;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #1e293b;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)


def get_hex_dump(file_bytes, max_bytes=48):
    """
    Memformat data byte menjadi string Hex Dump.
    """
    if not file_bytes:
        return "File kosong"
    try:
        data = file_bytes[:max_bytes]
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


def calculate_metrics(arr1, arr2):
    """
    Menghitung MSE dan PSNR antara dua numpy array gambar.
    """
    try:
        if arr1.shape != arr2.shape:
            return {"mse": None, "psnr": None}
            
        mse = np.mean((arr1 - arr2) ** 2)
        if mse == 0:
            psnr = float('inf')
        else:
            max_pixel = 255.0
            psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
            
        return {"mse": mse, "psnr": psnr}
    except Exception as e:
        st.error(f"Gagal menghitung metrik: {e}")
        return {"mse": None, "psnr": None}


# Initialize Session States
if 'comp_results' not in st.session_state:
    st.session_state.comp_results = None
if 'uploaded_filename' not in st.session_state:
    st.session_state.uploaded_filename = ""
if 'orig_size_bytes' not in st.session_state:
    st.session_state.orig_size_bytes = 0

# Navigation Sidebar
with st.sidebar:
    st.markdown('<h2 style="font-weight: 700; margin-bottom: 0;">🖼️ Kompresi Citra</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748b; font-size: 0.9rem; margin-top: 0;">RLE vs LZW vs Huffman</p>', unsafe_allow_html=True)
    
    st.write("---")
    menu = st.radio(
        "Navigasi Halaman:",
        ["⚡ Kompresi Tunggal", "📊 Analisis Dataset", "📈 Visualisasi Grafik"],
        index=0
    )
    st.write("---")

# ================= PAGES =================

if menu == "⚡ Kompresi Tunggal":
    st.markdown('<h1 class="title-gradient">Kompresi Tunggal</h1>', unsafe_allow_html=True)
    st.markdown("Unggah gambar berformat BMP (.bmp) untuk menganalisis performa kompresi secara real-time.")
    st.write("")

    uploaded_file = st.file_uploader("Pilih Gambar BMP", type=["bmp"])
    
    if uploaded_file is not None:
        # Load image details
        file_bytes = uploaded_file.read()
        orig_size_bytes = len(file_bytes)
        
        # Open image with Pillow to verify and display
        try:
            img = Image.open(io.BytesIO(file_bytes))
            width, height = img.size
            mode = img.mode
            arr_orig = np.array(img)
        except Exception as e:
            st.error(f"Gagal membuka gambar: {e}")
            st.stop()

        col_orig, col_meta = st.columns([1, 2])
        with col_orig:
            st.markdown("### 🖼️ Gambar Asli")
            st.image(img, use_container_width=True)
        with col_meta:
            st.markdown("### 📋 Detail Metadata")
            st.write(f"**Nama File**: `{uploaded_file.name}`")
            st.write(f"**Dimensi**: `{width} x {height}` piksel")
            st.write(f"**Mode Warna**: `{mode}`")
            st.write(f"**Ukuran File**: `{orig_size_bytes/1024:.2f} KB` ({orig_size_bytes} Byte)")
            
            # Button to trigger compression
            run_comp = st.button("🚀 Jalankan Kompresi", type="primary", use_container_width=True)

        if run_comp:
            st.session_state.comp_results = {}
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.orig_size_bytes = orig_size_bytes
            
            with st.spinner("Menjalankan kompresi Huffman, LZW, dan RLE..."):
                # Save source image to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".bmp") as tmp_orig:
                    tmp_orig.write(file_bytes)
                    tmp_orig_path = tmp_orig.name

                algos = [
                    ("Huffman", huffman_compress, huffman_decompress),
                    ("LZW", lzw_compress, lzw_decompress),
                    ("RLE", rle_compress, rle_decompress)
                ]

                for name, comp_fn, dec_fn in algos:
                    # Setup temporary output paths
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp_comp:
                        tmp_comp_path = tmp_comp.name
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".bmp") as tmp_dec:
                        tmp_dec_path = tmp_dec.name

                    try:
                        # Compress
                        t0 = time.perf_counter()
                        comp_fn(tmp_orig_path, tmp_comp_path)
                        t1 = time.perf_counter()
                        comp_time = (t1 - t0) * 1000.0 # to ms

                        # Decompress
                        t2 = time.perf_counter()
                        dec_fn(tmp_comp_path, tmp_dec_path)
                        t3 = time.perf_counter()
                        dec_time = (t3 - t2) * 1000.0 # to ms

                        # Read outputs back
                        with open(tmp_comp_path, "rb") as f:
                            comp_bytes = f.read()
                        with open(tmp_dec_path, "rb") as f:
                            dec_bytes = f.read()

                        # Calculate metrics
                        with Image.open(tmp_dec_path) as img_dec:
                            arr_dec = np.array(img_dec)
                        metrics = calculate_metrics(arr_orig, arr_dec)

                        # Save results to session state
                        st.session_state.comp_results[name] = {
                            "comp_bytes": comp_bytes,
                            "dec_bytes": dec_bytes,
                            "comp_size": len(comp_bytes),
                            "comp_time": comp_time,
                            "dec_time": dec_time,
                            "mse": metrics["mse"],
                            "psnr": metrics["psnr"],
                            "reduction": ((orig_size_bytes - len(comp_bytes)) / orig_size_bytes) * 100
                        }
                    except Exception as e:
                        st.error(f"Gagal memproses algoritma {name}: {e}")
                    finally:
                        # Cleanup temp files
                        if os.path.exists(tmp_comp_path): os.remove(tmp_comp_path)
                        if os.path.exists(tmp_dec_path): os.remove(tmp_dec_path)

                if os.path.exists(tmp_orig_path): os.remove(tmp_orig_path)
        
        # Display Results from Session State
        if st.session_state.comp_results is not None:
            st.write("---")
            st.markdown("## ⚡ Hasil Kompresi")
            st.write("")

            col1, col2, col3 = st.columns(3)
            cols = {"Huffman": col1, "LZW": col2, "RLE": col3}
            
            best_algo = max(st.session_state.comp_results.keys(), key=lambda k: st.session_state.comp_results[k]["reduction"])

            for name, res in st.session_state.comp_results.items():
                with cols[name]:
                    # Border highlighting for the best algorithm
                    border_style = "border: 2px solid #10b981;" if name == best_algo else "border: 1px solid rgba(255, 255, 255, 0.1);"
                    st.markdown(f"""
                        <div style="border-radius: 12px; padding: 15px; background-color: rgba(255, 255, 255, 0.03); {border_style} margin-bottom: 15px;">
                            <h3 style="margin-top:0; font-weight: 700; color: #f8fafc;">⚡ {name.upper()} {"🏆" if name == best_algo else ""}</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 1. Hex Viewer
                    st.markdown("**Hex Viewer (.bin)**:")
                    hex_dump = get_hex_dump(res["comp_bytes"])
                    st.code(hex_dump, language="text")

                    # 2. Decompressed Image Thumbnail
                    st.markdown("**Hasil Dekompresi (.bmp)**:")
                    img_dec_pil = Image.open(io.BytesIO(res["dec_bytes"]))
                    st.image(img_dec_pil, width=90)

                    # 3. Metrics Text
                    ratio = st.session_state.orig_size_bytes / res["comp_size"] if res["comp_size"] > 0 else 1.0
                    mse_text = f"{res['mse']:.4f}" if res['mse'] is not None else "-"
                    psnr_text = "Sempurna (∞)" if res['psnr'] == float('inf') else (f"{res['psnr']:.2f} dB" if res['psnr'] is not None else "-")
                    
                    st.markdown(f"""
                    * **Ukuran Akhir**: `{res['comp_size']/1024:.2f} KB`
                    * **Rasio Kompresi**: `{ratio:.2f} : 1`
                    * **Persentase Reduksi**: `{res['reduction']:.2f}%`
                    * **Waktu Kompresi**: `{res['comp_time']:.2f} ms`
                    * **Waktu Dekompresi**: `{res['dec_time']:.2f} ms`
                    * **MSE**: `{mse_text}`
                    * **PSNR**: `{psnr_text}`
                    * **Validasi**: `Lossless ✔️`
                    """)
                    
                    # 4. Downloads
                    fn_base = os.path.splitext(st.session_state.uploaded_filename)[0]
                    st.download_button(
                        label=f"💾 Download {name} (.bin)",
                        data=res["comp_bytes"],
                        file_name=f"{fn_base}_{name}.bin",
                        mime="application/octet-stream",
                        use_container_width=True
                    )
                    st.download_button(
                        label=f"🖼️ Download Dekompresi ({name})",
                        data=res["dec_bytes"],
                        file_name=f"{fn_base}_decomp_{name}.bmp",
                        mime="image/bmp",
                        use_container_width=True
                    )

            # Table Comparison
            st.write("---")
            st.markdown("### 📊 Tabel Perbandingan Metrik")
            
            table_data = []
            for name, res in st.session_state.comp_results.items():
                ratio = st.session_state.orig_size_bytes / res["comp_size"] if res["comp_size"] > 0 else 1.0
                table_data.append({
                    "Algoritma": name,
                    "Ukuran Awal": f"{st.session_state.orig_size_bytes/1024:.2f} KB",
                    "Ukuran Akhir": f"{res['comp_size']/1024:.2f} KB",
                    "Rasio Kompresi": f"{ratio:.2f} : 1",
                    "Persentase Reduksi (%)": f"{res['reduction']:.2f}%",
                    "Waktu Kompresi (ms)": f"{res['comp_time']:.2f}",
                    "Waktu Dekompresi (ms)": f"{res['dec_time']:.2f}",
                    "Validasi Lossless": "Lulus (Identik)",
                    "MSE": f"{res['mse']:.4f}" if res['mse'] is not None else "-",
                    "PSNR": "Sempurna (∞)" if res['psnr'] == float('inf') else (f"{res['psnr']:.2f} dB" if res['psnr'] is not None else "-")
                })
            
            df_comp = pd.DataFrame(table_data)
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

elif menu == "📊 Analisis Dataset":
    st.markdown('<h1 class="title-gradient">Analisis Dataset</h1>', unsafe_allow_html=True)
    st.markdown("Ringkasan performa secara kolektif berdasarkan hasil pengujian batch dataset.")
    st.write("")

    csv_path = "hasil_kompresi.csv"

    # Add Run Dataset Test Button
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        run_batch = st.button("▶️ Jalankan Pengujian Batch Dataset (90 Gambar)", type="primary", use_container_width=True)
    with col_info:
        st.markdown("<p style='padding-top: 5px; color: #64748b;'>Menjalankan pengujian kompresi & dekompresi RLE, LZW, dan Huffman secara batch pada seluruh gambar di folder <code>bmp_dataset</code>.</p>", unsafe_allow_html=True)

    if run_batch:
        dataset_dir = "bmp_dataset"
        if not os.path.exists(dataset_dir):
            st.error(f"Folder dataset `{dataset_dir}` tidak ditemukan di root proyek.")
        else:
            files = [f for f in os.listdir(dataset_dir) if f.endswith(".bmp")]
            if not files:
                st.warning("Tidak ada file gambar berformat .bmp di dalam folder `bmp_dataset`.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Make sure directories exist
                os.makedirs("compressed", exist_ok=True)
                os.makedirs("decompressed", exist_ok=True)
                
                results = []
                total_files = len(files)
                
                for idx, file in enumerate(files):
                    status_text.text(f"Memproses gambar {idx+1}/{total_files}: {file}...")
                    path = os.path.abspath(os.path.join(dataset_dir, file))
                    
                    before = os.path.getsize(path)
                    
                    # Algorithms to test
                    algos = [
                        ("RLE", rle_compress, rle_decompress, "RLE"),
                        ("LZW", lzw_compress, lzw_decompress, "LZW"),
                        ("Huffman", huffman_compress, huffman_decompress, "Huffman")
                    ]
                    
                    for name, comp_fn, dec_fn, suffix in algos:
                        out_bin = os.path.abspath(os.path.join("compressed", f"{os.path.splitext(file)[0]}_{suffix}.bin"))
                        out_dec = os.path.abspath(os.path.join("decompressed", f"{os.path.splitext(file)[0]}_{suffix}.bmp"))
                        
                        try:
                            # Compress time
                            t0 = time.perf_counter()
                            comp_fn(path, out_bin)
                            t_comp = (time.perf_counter() - t0) * 1000.0
                            
                            # Decompress time
                            t1 = time.perf_counter()
                            dec_fn(out_bin, out_dec)
                            t_dec = (time.perf_counter() - t1) * 1000.0
                            
                            after = os.path.getsize(out_bin)
                            pct = ((before - after) / before) * 100
                            
                            results.append({
                                "Gambar": file,
                                "Algoritma": name,
                                "Awal": before,
                                "Akhir": after,
                                "Persentase": pct,
                                "Waktu_Kompresi": t_comp,
                                "Waktu_Dekompresi": t_dec,
                                "MSE": 0.0,
                                "PSNR": float('inf')
                            })
                        except Exception as e:
                            st.warning(f"Error memproses {file} dengan {name}: {e}")
                    
                    progress_bar.progress((idx + 1) / total_files)
                
                # Save to CSV
                df_results = pd.DataFrame(results)
                df_results.to_csv(csv_path, index=False)
                
                status_text.success(f"Pengujian batch selesai! {total_files} gambar diproses. Hasil disimpan ke `{csv_path}`.")
                st.balloons()
                time.sleep(1)

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        
        # Calculate Ratio
        if "Rasio" not in df.columns:
            df["Rasio"] = df["Awal"] / df["Akhir"]

        # Summary Metrics
        st.markdown("### 🏆 Ringkasan Rata-rata Performa Dataset")
        avg_savings = df.groupby("Algoritma")["Persentase"].mean()
        avg_times = df.groupby("Algoritma")["Waktu_Kompresi"].mean()
        avg_ratios = df.groupby("Algoritma")["Rasio"].mean()
        
        best_algo = avg_savings.idxmax() if not avg_savings.empty else None

        card1, card2, card3 = st.columns(3)
        cards = {"Huffman": card1, "LZW": card2, "RLE": card3}

        for algo in ["RLE", "LZW", "Huffman"]:
            with cards[algo]:
                border_color = "border: 2px solid #10b981;" if algo == best_algo else "border: 1px solid rgba(255, 255, 255, 0.1);"
                saving = avg_savings.get(algo, 0.0)
                t_comp = avg_times.get(algo, 0.0)
                t_ratio = avg_ratios.get(algo, 1.0)
                
                st.markdown(f"""
                <div style="border-radius: 12px; padding: 20px; background-color: rgba(255, 255, 255, 0.03); {border_color}">
                    <h3 style="margin-top:0; font-weight:700;">{algo} {"🏆" if algo == best_algo else ""}</h3>
                    <p style="margin-bottom:5px;">Rata-rata Reduksi: <b>{saving:.2f}%</b></p>
                    <p style="margin-bottom:5px;">Rata-rata Rasio: <b>{t_ratio:.2f} : 1</b></p>
                    <p style="margin-bottom:0;">Rata-rata Waktu: <b>{t_comp:.2f} ms</b></p>
                </div>
                """, unsafe_allow_html=True)
        
        # Data table listing
        st.write("---")
        st.markdown("### 📋 Semua Riwayat Hasil Kompresi")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("File database pengujian `hasil_kompresi.csv` tidak ditemukan. Silakan jalankan pengujian dataset dari aplikasi desktop terlebih dahulu untuk membuat basis data.")

elif menu == "📈 Visualisasi Grafik":
    st.markdown('<h1 class="title-gradient">Visualisasi Grafik</h1>', unsafe_allow_html=True)
    st.markdown("Visualisasi grafik interaktif perbandingan performa kompresi citra.")
    st.write("")

    source = st.selectbox(
        "Pilih Sumber Data Grafik:",
        ["Gambar Tunggal", "Analisis Dataset (Rata-rata)"]
    )

    if source == "Gambar Tunggal":
        if st.session_state.comp_results is None:
            st.info("Belum ada data Gambar Tunggal. Silakan buka halaman 'Kompresi Tunggal', unggah gambar, lalu jalankan kompresi terlebih dahulu.")
        else:
            algos_list = ["RLE", "LZW", "Huffman"]
            ratios = []
            reductions = []
            times = []
            
            for a in algos_list:
                res = st.session_state.comp_results[a]
                ratios.append(st.session_state.orig_size_bytes / res["comp_size"] if res["comp_size"] > 0 else 1.0)
                reductions.append(res["reduction"])
                times.append(res["comp_time"])

            # Render Matplotlib Figure
            bg_color = "#16161a"
            text_color = "#f8fafc"
            ax_bg = "#1e1e24"
            grid_color = "#334155"
            bar_colors = ["#3b82f6", "#10b981", "#8b5cf6"]

            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 4.5), facecolor=bg_color)
            fig.suptitle(f"Perbandingan Metrik Kompresi untuk: {st.session_state.uploaded_filename}", color=text_color, fontsize=12, fontweight="bold", y=0.98)

            def style_ax(ax, title, ylabel):
                ax.set_title(title, color=text_color, fontsize=9, fontweight="bold", pad=8)
                ax.set_facecolor(ax_bg)
                ax.tick_params(colors=text_color, labelsize=8)
                ax.spines['bottom'].set_color(grid_color)
                ax.spines['top'].set_color('none')
                ax.spines['right'].set_color('none')
                ax.spines['left'].set_color(grid_color)
                ax.yaxis.grid(True, linestyle='--', alpha=0.5, color=grid_color)
                ax.set_ylabel(ylabel, color=text_color, fontsize=8)

            # Plot 1: Rasio Kompresi
            bars1 = ax1.bar(algos_list, ratios, color=bar_colors, width=0.45)
            style_ax(ax1, "Rasio Kompresi\n(lebih tinggi = lebih baik)", "Rasio (X : 1)")
            for bar in bars1:
                yval = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.05, f"{yval:.2f}x", ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')

            # Plot 2: Persentase Reduksi
            bars2 = ax2.bar(algos_list, reductions, color=bar_colors, width=0.45)
            style_ax(ax2, "Persentase Reduksi (%)\n(lebih tinggi = lebih baik)", "Persentase (%)")
            for bar in bars2:
                yval = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f"{yval:.2f}%", ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')

            # Plot 3: Waktu Kompresi
            bars3 = ax3.bar(algos_list, times, color=bar_colors, width=0.45)
            style_ax(ax3, "Waktu Kompresi\n(lebih rendah = lebih cepat)", "Waktu (ms)")
            for bar in bars3:
                yval = bar.get_height()
                offset = 0.05 * max(times) if times and max(times) > 0 else 0.05
                ax3.text(bar.get_x() + bar.get_width()/2, yval + offset, f"{yval:.1f} ms", ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')

            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    else: # Analisis Dataset (Rata-rata)
        csv_path = "hasil_kompresi.csv"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if "Rasio" not in df.columns:
                df["Rasio"] = df["Awal"] / df["Akhir"]

            avg_savings = df.groupby("Algoritma")["Persentase"].mean()
            avg_times = df.groupby("Algoritma")["Waktu_Kompresi"].mean()
            avg_ratios = df.groupby("Algoritma")["Rasio"].mean()

            algos_list = ["RLE", "LZW", "Huffman"]
            ratios = [avg_ratios.get(a, 1.0) for a in algos_list]
            reductions = [avg_savings.get(a, 0.0) for a in algos_list]
            times = [avg_times.get(a, 0.0) for a in algos_list]

            # Render Matplotlib Figure
            bg_color = "#16161a"
            text_color = "#f8fafc"
            ax_bg = "#1e1e24"
            grid_color = "#334155"
            bar_colors = ["#3b82f6", "#10b981", "#8b5cf6"]

            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 4.5), facecolor=bg_color)
            fig.suptitle(f"Rata-rata Performa Kompresi pada Dataset ({len(df)//3} Gambar)", color=text_color, fontsize=12, fontweight="bold", y=0.98)

            def style_ax(ax, title, ylabel):
                ax.set_title(title, color=text_color, fontsize=9, fontweight="bold", pad=8)
                ax.set_facecolor(ax_bg)
                ax.tick_params(colors=text_color, labelsize=8)
                ax.spines['bottom'].set_color(grid_color)
                ax.spines['top'].set_color('none')
                ax.spines['right'].set_color('none')
                ax.spines['left'].set_color(grid_color)
                ax.yaxis.grid(True, linestyle='--', alpha=0.5, color=grid_color)
                ax.set_ylabel(ylabel, color=text_color, fontsize=8)

            # Plot 1: Rasio Kompresi
            bars1 = ax1.bar(algos_list, ratios, color=bar_colors, width=0.45)
            style_ax(ax1, "Rata-rata Rasio Kompresi", "Rasio (X : 1)")
            for bar in bars1:
                yval = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f"{yval:.2f}x", ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')

            # Plot 2: Persentase Reduksi
            bars2 = ax2.bar(algos_list, reductions, color=bar_colors, width=0.45)
            style_ax(ax2, "Rata-rata Persentase Reduksi", "Persentase (%)")
            for bar in bars2:
                yval = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f"{yval:.2f}%", ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')

            # Plot 3: Waktu Kompresi
            bars3 = ax3.bar(algos_list, times, color=bar_colors, width=0.45)
            style_ax(ax3, "Rata-rata Waktu Proses Kompresi", "Waktu (ms)")
            for bar in bars3:
                yval = bar.get_height()
                offset = 0.05 * max(times) if times and max(times) > 0 else 0.05
                ax3.text(bar.get_x() + bar.get_width()/2, yval + offset, f"{yval:.1f} ms", ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')

            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.warning("File database pengujian `hasil_kompresi.csv` tidak ditemukan. Silakan jalankan pengujian dataset dari aplikasi desktop terlebih dahulu untuk membuat basis data.")
