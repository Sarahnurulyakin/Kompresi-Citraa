# 🖼️ Studi Komparasi Algoritma Kompresi Citra (RLE vs LZW vs Huffman)

Aplikasi desktop berbasis GUI (Graphical User Interface) untuk mengompresi dan menganalisis performa algoritma kompresi citra lossless (**Run-Length Encoding, Lempel-Ziv-Welch, dan Huffman Coding**) pada citra berformat BMP. Proyek ini dibuat sebagai **Project Akhir Mata Kuliah Sistem Multimedia (Semester 6)** di Program Studi Teknik Informatika, UIN Sunan Gunung Djati Bandung.

---

## 🚀 Fitur Utama

1. **Kompresi Tunggal (Single Compression)**
   * Memilih citra BMP secara interaktif.
   * Menjalankan kompresi dan dekompresi secara instan menggunakan 3 algoritma sekaligus (RLE, LZW, Huffman).
   * Menampilkan perbandingan performa (*Original Size, Compressed Size, Compression Ratio, Space Saving, Compression Time,* dan *Decompression Time*).
   * Validasi kecocokan byte hasil dekompresi dengan file asli secara otomatis (*Lossless Validation*).
   * Menampilkan pratinjau (*preview*) visual perbandingan citra sebelum dan sesudah kompresi.

2. **Analisis Dataset (Batch Testing)**
   * Menjalankan uji performa massal secara otomatis terhadap seluruh dataset gambar di folder `bmp_dataset`.
   * Menghasilkan file laporan `hasil_kompresi.csv` berisi metrik pengujian lengkap.
   * Menampilkan tabel performa keseluruhan dan ringkasan rata-rata *saving* serta waktu kompresi per algoritma langsung di dalam aplikasi.

3. **Dashboard Premium Terpisah**
   * Aplikasi dashboard visual interaktif khusus (`gui/dashboard.py`) untuk mempresentasikan data hasil pengujian dataset secara rapi dan profesional.
   * Dilengkapi fitur pencarian citra, kartu ringkasan algoritma terbaik (*Highest Saving*), dan visualisasi komparasi gambar asli vs hasil dekompresi beserta metrik performanya secara detail.

4. **Konverter Gambar Ke BMP**
   * Script utilitas untuk mengubah gambar berformat PNG/JPG dalam folder `dataset` menjadi format BMP (24-bit/RGB) di folder `bmp_dataset` secara otomatis agar siap digunakan dalam pengujian kompresi.

---

## 🛠️ Teknologi & Library

Proyek ini dibangun menggunakan bahasa pemrograman **Python 3** dengan library berikut:
* **CustomTkinter (v5.2.2)**: Pembuatan antarmuka (GUI) modern dengan tema Gelap/Terang.
* **Pillow (v12.2.0)**: Pengolahan dan manipulasi gambar.
* **Pandas (v3.0.3)**: Pengolahan data tabel dan pembuatan file laporan CSV.
* **Numpy (v2.4.6)**: Komputasi numerik pendukung.

---

## 📁 Struktur Direktori

```text
KompresiCitra/
├── algorithms/               # Implementasi Algoritma Kompresi
│   ├── __init__.py
│   ├── huffman.py            # Huffman Coding
│   ├── lzw.py                # Lempel-Ziv-Welch (16-bit)
│   └── rle.py                # Run-Length Encoding
├── gui/                      # Antarmuka Pengguna (GUI)
│   ├── app.py                # Aplikasi Utama (Single & Batch Test)
│   └── dashboard.py          # Dashboard Visual Presentasi Premium
├── dataset/                  # Gambar mentah (PNG, JPG) sebelum konversi
├── bmp_dataset/              # Dataset gambar dalam format BMP (siap diuji)
├── compressed/               # Hasil file terkompresi (.bin)
├── decompressed/             # Hasil gambar hasil dekompresi (.bmp)
├── venv/                     # Virtual Environment Python
├── main.py                   # File entry point aplikasi utama
├── convert_to_bmp.py         # Skrip konversi gambar ke format BMP
├── batch_test.py             # Skrip pengujian CLI massal
├── hasil_kompresi.csv        # Log data hasil pengujian kompresi
├── requirements.txt          # Daftar dependencies proyek
├── test_rle.py               # Uji coba sederhana RLE
├── test_lzw.py               # Uji coba sederhana LZW
└── test_huffman.py           # Uji coba sederhana Huffman
```

---

## ⚙️ Penjelasan Algoritma Kompresi

### 1. Run-Length Encoding (RLE)
Algoritma kompresi lossless sederhana yang bekerja dengan mendeteksi barisan data (byte) berturut-turut yang bernilai sama (*runs*) dan menggantinya dengan sepasang nilai: **[Jumlah Kejadian (Count), Nilai Byte (Value)]**. 
* **Karakteristik**: Sangat efektif untuk citra yang memiliki area warna solid yang luas (seperti ilustrasi atau logo), namun bisa menghasilkan ukuran file yang lebih besar jika citra memiliki gradasi warna atau detail yang tinggi (seperti foto pemandangan).
* **Batas Count**: Maksimum 255 per run (disimpan dalam 1 byte).

### 2. Lempel-Ziv-Welch (LZW)
Algoritma kompresi berbasis kamus (*dictionary-based*). LZW membaca data secara berurutan dan mengelompokkan karakter/byte menjadi string baru. Jika string belum ada di kamus, string tersebut ditambahkan ke kamus dengan kode index baru, dan kode dari string sebelumnya akan ditulis ke file output.
* **Karakteristik**: Kamus dinamis diinisialisasi dengan 256 nilai dasar byte tunggal. 
* **Format Output**: Menggunakan representasi kode 16-bit (`>H` atau unsigned short big-endian), dengan kapasitas kamus maksimum hingga 65.535 entri. Sangat bagus dalam mengompresi data dengan pola berulang.

### 3. Huffman Coding
Algoritma kompresi berbasis frekuensi kemunculan simbol. Karakter/byte yang paling sering muncul akan mendapatkan representasi kode biner yang lebih pendek, sedangkan byte yang jarang muncul mendapatkan kode biner yang lebih panjang (Variable-Length Code).
* **Karakteristik**: Menggunakan struktur data *Binary Tree* (Pohon Huffman) dan *Priority Queue* (Heap) untuk membangun kode biner optimal. 
* **Format Output**: Kode biner beserta tabel/kamus kode Huffman disimpan menggunakan modul `pickle` agar dapat didekompresi kembali secara utuh.

---

## 💻 Cara Instalasi & Penggunaan

### 1. Kloning Repositori
```bash
git clone https://github.com/Sarahnurulyakin/Kompresi-Citraa.git
cd Kompresi-Citraa
```

### 2. Setup Virtual Environment (Opsional tetapi Direkomendasikan)
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalasi Dependencies
```bash
pip install -r requirements.txt
```

### 4. Persiapan Dataset BMP (Jika Belum Ada)
Letakkan gambar `.png` atau `.jpg` di folder `dataset`, kemudian jalankan skrip berikut untuk mengonversinya menjadi format `.bmp` secara otomatis:
```bash
python convert_to_bmp.py
```
*Hasil konversi akan disimpan di folder `bmp_dataset`.*

### 5. Menjalankan Aplikasi Utama (GUI)
Aplikasi utama menyediakan fitur kompresi untuk gambar tunggal serta pengujian batch dataset.
```bash
python main.py
```

### 6. Menjalankan Dashboard Presentasi (GUI)
Dashboard interaktif premium untuk memvisualisasikan hasil pengujian dataset secara elegan.
```bash
python gui/dashboard.py
```

---

## 📈 Metrik Evaluasi Performa
Aplikasi ini menghitung performa kompresi berdasarkan beberapa rumus standar:
* **Ukuran Awal & Akhir**: Dihitung dalam satuan *Kilobyte (KB)* atau *Bytes*.
* **Rasio Kompresi (Compression Ratio)**:
  $$\text{Rasio} = \frac{\text{Ukuran Awal}}{\text{Ukuran Akhir}}$$
* **Penghematan Ruang (Space Saving %)**:
  $$\text{Space Saving (\%)} = \left( \frac{\text{Ukuran Awal} - \text{Ukuran Akhir}}{\text{Ukuran Awal}} \right) \times 100\%$$
* **Kecepatan Proses**: Dihitung menggunakan objek waktu berpresisi tinggi `time.perf_counter()` dalam satuan *milidetik (ms)*.
* **Integritas Data (Validation)**: Memeriksa apakah byte gambar hasil dekompresi identik 100% dengan file asli (`f1.read() == f2.read()`).

---

## 👤 Identitas Pengembang
* **Nama**: Sarah Nurul Yakin
* **Prodi**: Teknik Informatika
* **Institusi**: UIN Sunan Gunung Djati Bandung
* **Mata Kuliah**: Sistem Multimedia (Semester 6)
