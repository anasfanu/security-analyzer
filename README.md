# 🔒 SYKIL : Security Analyzer

> **Smashing Vulnerabilities, Securing Code**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE.md)
[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](#)

**SYKIL** adalah alat keamanan (*security tools*) canggih berbasis CLI yang dirancang untuk mendeteksi kerentanan, bug, dan anomali dalam kode sumber Anda. Mendukung analisis mendalam untuk bahasa pemrograman PHP, JavaScript, Python, Java, Ruby, serta berbagai framework modern.

---

## ✨ Fitur Utama

* 🔍 **36+ Security Rules** – Deteksi kerentanan OWASP Top 10 dan CVE spesifik.
* 🛡️ **8 CVE Detection** – Mengidentifikasi PHP2Shell, Next.js SSRF, Django SQLi, Spring RCE, dll.
* 🔧 **Auto-Fix Engine** – Solusi perbaikan otomatis untuk 19+ jenis masalah keamanan.
* 📝 **Multi-Format Report** – Output hasil scan berupa format Console berwarna, JSON, dan HTML.
* 🔐 **Credential Migration** – Migrasi otomatis *hardcoded credentials* langsung ke file `.env`.
* 📊 **Statistik Lengkap** – *Breakdown* analisis berdasarkan tingkat keparahan (*severity*), kategori, dan file.
* 💾 **Backup System** – Pencadangan otomatis sebelum mekanisme *auto-fix* dijalankan.
* 📋 **Manual Fix Guide** – Menyediakan panduan manual khusus untuk menangani *issue* yang kompleks.
* 🔄 **Dry-Run Mode** – Pratinjau (*preview*) perbaikan tanpa mengubah file asli Anda.
* 🎯 **Interactive Mode** – Konfirmasi tindakan manual secara interaktif per kasus yang ditemukan.

---

## 🚀 Instalasi

### Dari PyPI (Coming Soon)
```bash
pip install sykil-security-analyzer
```

### Dari Source (Local Development)
```bash
git clone https://github.com/anasfanu/sykil-security-analyzer.git
cd sykil-security-analyzer
pip install -e .
```

---

## 📖 Cara Penggunaan

### 1. Scan Project
```bash
# Scan folder saat ini
sykil .

# Scan folder spesifik
sykil /path/to/project

# Scan dengan export JSON
sykil /path/to/project --export json

# Scan dengan export HTML
sykil /path/to/project --export html

# Scan dengan export keduanya (JSON & HTML)
sykil /path/to/project --export both
```

### 2. Auto-Fix
```bash
# Preview fix (dry-run, aman digunakan)
sykil --fix output/sykil_report_xxx.json --dry-run

# Jalankan auto-fix normal
sykil --fix output/sykil_report_xxx.json

# Auto-fix interaktif (konfirmasi per issue)
sykil --fix output/sykil_report_xxx.json --interactive

# Auto-fix dengan ekspor statistik tambahan
sykil --fix output/sykil_report_xxx.json --export-stats
```

### 3. Manajemen Log & Bantuan
```bash
# Lihat log aktivitas aplikasi
sykil --view-logs app

# Lihat 100 baris terakhir log error
sykil --view-logs error --log-lines 100

# Menampilkan menu bantuan dan versi
sykil --help
sykil --version
```

---

## 🛡️ Kerentanan yang Dideteksi

### Security Issues Umum

| ID | Kategori | Severity |
| :--- | :--- | :--- |
| **SEC-001** | Hardcoded Credentials | 🔴 CRITICAL |
| **SEC-002** | SQL Injection | 🟠 HIGH |
| **SEC-003** | Cross-Site Scripting (XSS) | 🟠 HIGH |
| **SEC-004** | Remote Code Execution (eval) | 🔴 CRITICAL |
| **SEC-005** | Command Injection | 🔴 CRITICAL |
| **SEC-006** | File Inclusion (LFI/RFI) | 🔴 CRITICAL |
| **SEC-007** | Path Traversal | 🟠 HIGH |
| **SEC-008** | Insecure Deserialization | 🟠 HIGH |
| **SEC-009** | Weak Cryptography | 🟡 MEDIUM |
| **SEC-010** | Insecure Random Number | 🟡 MEDIUM |
| **SEC-011** | Debug Functions | 🔵 LOW |
| **SEC-012** | Insecure Cookie | 🟡 MEDIUM |
| **SEC-013** | Missing Security Headers | 🟡 MEDIUM |
| **SEC-014** | Open Redirect | 🟠 HIGH |
| **SEC-015** | XML External Entity (XXE) | 🟠 HIGH |
| **SEC-016** | Server-Side Request Forgery | 🟠 HIGH |
| **SEC-017** | Information Disclosure | 🟡 MEDIUM |
| **SEC-018** | Insecure File Upload | 🟡 MEDIUM |
| **SEC-019** | Loose Comparison | 🔵 LOW |
| **SEC-020** | Unsafe File Operations | 🟡 MEDIUM |
| **SEC-021** | Insecure Direct Object Reference | 🟠 HIGH |
| **SEC-022** | CORS Misconfiguration | 🟡 MEDIUM |
| **SEC-023** | Weak SSL/TLS Configuration | 🟠 HIGH |
| **SEC-024** | Directory Listing Enabled | 🟡 MEDIUM |
| **SEC-025** | Console Logging | 🔵 LOW |
| **SEC-026** | Unsafe eval in JavaScript | 🟠 HIGH |
| **SEC-027** | InnerHTML XSS | 🟡 MEDIUM |
| **SEC-028** | Document.write XSS | 🟠 HIGH |
| **SEC-029** | LocalStorage Sensitive Data | 🟡 MEDIUM |
| **SEC-030** | Insecure HTTP Request | 🟠 HIGH |

### CVE Spesifik

| CVE | Kategori | Severity |
| :--- | :--- | :--- |
| **CVE-2026-111497** | HTTP2Shell / Node2Shell / Broccoli2Shell | 🔴 CRITICAL |
| **CVE-2026-109618** | PHP2Shell | 🔴 CRITICAL |
| **CVE-2026-109619** | PHP2Shell Variant | 🔴 CRITICAL |
| **CVE-2026-63030** | wp2shell (WebShell Upload) | 🔴 CRITICAL |
| **CVE-2026-60137** | wp2shell Variant | 🔴 CRITICAL |
| **CVE-2024-38816** | Spring Framework RCE | 🟠 HIGH |
| **CVE-2024-4007** | Laravel Session Bypass | 🟡 MEDIUM |
| **CVE-2024-34342** | Next.js SSR SSRF | 🟠 HIGH |
| **CVE-2024-42005** | Django SQL Injection | 🟠 HIGH |
| **CVE-2024-26143** | Ruby on Rails ReDoS | 🟡 MEDIUM |

---

## 🔧 Kemampuan Auto-Fix

### ⚡ Level 1: Deterministic Fix (100% Aman)
* ✅ **SEC-009:** Weak Cryptography $\rightarrow$ Diubah ke `password_hash()`
* ✅ **SEC-011:** Debug Functions $\rightarrow$ Menghapus baris debug
* ✅ **SEC-012:** Insecure Cookie $\rightarrow$ Menambahkan flag keamanan pada cookie
* ✅ **SEC-019:** Loose Comparison $\rightarrow$ Mengubah `==` menjadi `===`
* ✅ **SEC-020:** Unsafe File Operations $\rightarrow$ Mengamankan permission ke `0755`
* ✅ **SEC-022:** CORS Wildcard $\rightarrow$ Mengubah wildcard ke domain spesifik
* ✅ **SEC-023:** SSL Verify False $\rightarrow$ Mengubah konfigurasi menjadi `true`
* ✅ **SEC-024:** Directory Listing $\rightarrow$ Menambahkan opsi `-Indexes`
* ✅ **SEC-025:** Console Logging $\rightarrow$ Menghapus *statement* log konsol
* ✅ **SEC-030:** HTTP $\rightarrow$ Memaksa pengalihan ke HTTPS

### 🧠 Level 2: Context-Aware Fix (90% Aman)
* ✅ **SEC-001:** Hardcoded Credentials $\rightarrow$ Otomatis migrasi variabel sensitif ke `.env`
* ✅ **SEC-003:** XSS Output $\rightarrow$ Membungkus output dengan fungsi `htmlspecialchars()`
* ✅ **SEC-010:** Insecure Random $\rightarrow$ Mengganti ke generator aman `random_int()`
* ✅ **SEC-013:** Missing Headers $\rightarrow$ Menginjeksi *security headers* yang direkomendasikan
* ✅ **SEC-017:** Information Disclosure $\rightarrow$ Mematikan penampilan display errors
* ✅ **SEC-026:** JS eval $\rightarrow$ Memberikan komentar (comment out) + tanda `// TODO:`
* ✅ **SEC-027:** innerHTML $\rightarrow$ Mengubah manipulasi DOM ke `textContent`
* ✅ **SEC-028:** document.write $\rightarrow$ Memberikan komentar (comment out) pada baris terkait
* ✅ **SEC-029:** LocalStorage $\rightarrow$ Memberikan catatan migrasi (migration note)

> ⚠️ **Manual Fix Required:** Untuk jenis kerentanan tingkat lanjut yang lebih kompleks seperti *SQL Injection*, *Remote Code Execution (RCE)*, dan beberapa *CVE spesifik*, SYKIL akan menyediakan panduan perbaikan manual yang sangat komprehensif di dalam file `MANUAL_FIXES.md`.

---

## 📝 Lisensi

Didistribusikan di bawah lisensi MIT. Silakan periksa file [LICENSE.md](./LICENSE.md).
