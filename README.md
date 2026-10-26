# 🔒 Deep Project Security & Bug Analyzer

[![License: MIT](https://shields.io)](https://opensource.org)
[![Python Version](https://shields.io)](https://python.org)

**Deep Project Security & Bug Analyzer** adalah *tool* keamanan mutakhir yang dirancang khusus untuk mendeteksi kerentanan, bug, dan anomali secara mendalam di dalam kode sumber Anda. 

---

## ✨ Fitur Unggulan

* **Deteksi CVE Spesifik:** Identifikasi instan terhadap PHP2Shell, Next.js SSRF, Django SQLi, dan berbagai kerentanan kritis lainnya.
* **Auto-Fix Engine:** Memperbaiki celah keamanan secara otomatis dengan sistem *backup* yang aman.
* **Multi-Format Output:** Ekspor hasil pemindaian ke dalam format **Console**, **JSON**, atau **HTML**.
* **Fleksibilitas Antarmuka:** Jalankan pemindaian secara fleksibel melalui **CLI Mode** (Terminal) atau **Web Interface** (Browser).
* **Indikator Progres Real-Time:** Pantau jalannya proses pemindaian secara langsung.
* **Dukungan Whitelist:** Lewati baris kode tertentu yang aman menggunakan anotasi komentar `@nosec`.

---

## 🚀 Panduan Instalasi

Ikuti langkah-langkah berikut untuk memasang project di lingkungan lokal Anda:

```bash
# 1. Klon atau unduh repositori ini
git clone https://github.com
cd security_analyzer

# 2. Buat & aktifkan virtual environment (Opsional tetapi disarankan)
python -m venv venv
# Untuk Linux/Mac:
source venv/bin/activate 
# Untuk Windows:
venv\Scripts\activate

# 3. Instal semua dependensi yang diperlukan
pip install -r requirements.txt
```

---

## 📖 Cara Penggunaan

### 💻 Mode CLI (Command Line Interface)

Jalankan pemindaian dasar atau lakukan ekspor laporan langsung melalui terminal Anda:

```bash
# Pemindaian direktori standar
python main.py /path/to/project

# Pemindaian dengan ekspor laporan (JSON / HTML / Keduanya)
python main.py /path/to/project --export json
python main.py /path/to/project --export html
python main.py /path/to/project --export both

# Menerapkan perbaikan otomatis berdasarkan laporan JSON
python main.py --fix output/scan_report_20261027_120000.json
```

### 🌐 Mode Web

Aktifkan antarmuka berbasis web untuk pengalaman pemindaian visual yang lebih interaktif:

```bash
# Jalankan server aplikasi web
python web_app.py
```
Setelah server aktif, buka browser Anda dan akses: `http://localhost:5000`

---

## 🛠️ Panduan Perintah (CLI Reference)

Security Analyzer menyediakan berbagai opsi perintah untuk memindai proyek, mengekspor laporan, memperbaiki masalah, dan memeriksa log aplikasi melalui terminal.

### 📋 Daftar Opsi & Argumen

| Opsi / Argumen | 🛠️ Fungsi & Kegunaan | 💻 Contoh Sintaks Perintah |
|:---|:---|:---|
| `python main.py .` | Memindai direktori aktif saat ini. | `python main.py .` |
| `python main.py <path>` | Memindai direktori spesifik yang dipilih. | `python main.py C:\project\saya` |
| `--export json` | Mengekspor laporan hasil pemindaian ke format JSON. | `python main.py . --export json` |
| `--export html` | Mengekspor laporan visual ke format HTML. | `python main.py . --export html` |
| `--export both` | Mengekspor laporan ke format JSON dan HTML sekaligus. | `python main.py . --export both` |
| `--fix <file>` | Memperbaiki celah secara otomatis berdasarkan laporan JSON. | `python main.py --fix output/report.json` |
| `--view-logs app` | Menampilkan seluruh riwayat log aplikasi. | `python main.py --view-logs app` |
| `--view-logs error` | Menampilkan log khusus aktivitas error. | `python main.py --view-logs error` |
| `--log-lines N` | Membatasi jumlah baris log yang ditampilkan. | `python main.py --view-logs app --log-lines 200` |
| `--help` | Menampilkan dokumentasi bantuan di terminal. | `python main.py --help` |

### 🚀 Contoh Penggunaan

**1. Memindai proyek dan mengekspor laporan**

```bash
# Memindai direktori saat ini dan menyimpan laporan JSON
python main.py . --export json

# Memindai direktori tertentu dan mengekspor laporan HTML
python main.py C:\project\saya --export html

# Mengekspor laporan dalam kedua format
python main.py . --export both
```

**2. Memperbaiki masalah berdasarkan laporan**

```bash
python main.py --fix output/report.json
```

**3. Memeriksa log aplikasi**

```bash
# Menampilkan log aplikasi
python main.py --view-logs app

# Menampilkan log error
python main.py --view-logs error

# Menampilkan maksimal 200 baris log aplikasi
python main.py --view-logs app --log-lines 200
```

**4. Melihat dokumentasi bantuan**

```bash
python main.py --help
```

> **💡 Tips:** Jalankan `python main.py --help` untuk melihat opsi bantuan yang tersedia pada aplikasi.

---

## 🛡️ CVE yang Didukung

Aplikasi ini dilengkapi dengan pustaka deteksi untuk berbagai kerentanan populer dan terbaru:

| Kode CVE | Nama / Deskripsi Kerentanan |
| :--- | :--- |
| **CVE-2026-111497** | HTTP2Shell / Node2Shell / Broccoli2Shell |
| **CVE-2026-109618** | PHP2Shell Remote Code Execution (RCE) |
| **CVE-2026-63030**  | wp2shell WordPress Vulnerability |
| **CVE-2024-38816**  | Spring Framework RCE |
| **CVE-2024-4007**   | Laravel Session Bypass |
| **CVE-2024-34342**  | Next.js SSR SSRF |
| **CVE-2024-42005**  | Django SQL Injection |
| **CVE-2024-26143**  | Ruby on Rails ReDoS |

---

## 📝 Lisensi

Didistribusikan di bawah **[MIT License](LICENSE.md)**.
