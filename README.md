# 🧹 UClean — Ubuntu System Cleaner

Aplikasi GUI sederhana untuk membersihkan sampah sistem Ubuntu **dengan satu klik**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Ubuntu%20%7C%20Debian-orange.svg)
![Python](https://img.shields.io/badge/python-3.6%2B-green.svg)

---

## ✨ Fitur

| Item | Keterangan |
|------|-----------|
| 📦 APT Cache | Cache paket apt yang sudah diunduh |
| 🗑️ Orphan Packages | Dependensi yang tidak dibutuhkan (`autoremove`) |
| 📋 Journal Log Lama | Log sistem lebih dari 7 hari |
| 🗑️ Trash / Sampah | File di tempat sampah |
| 🖼️ Thumbnail Cache | Cache gambar preview file manager |
| 📦 Snap Versi Lama | Versi snap yang sudah dinonaktifkan |

---

## 📸 Screenshot

> GTK3 native UI — tampil seperti aplikasi Ubuntu asli.
> <img width="565" height="578" alt="Screenshot From 2026-05-04 15-25-36" src="https://github.com/user-attachments/assets/61ee8633-e4e8-48d8-92c7-ba8e4305e6ab" />


---

## 📦 Instalasi (direkomendasikan)

Download file `.deb` dari [Releases](https://github.com/orchivillando/uclean/releases) lalu:

```bash
sudo dpkg -i uclean_1.0.0_all.deb
sudo apt-get install -f   # install dependensi jika ada yang kurang
```

Setelah install, buka dari **Application Menu** atau jalankan:

```bash
uclean
```

---

## 🛠️ Instalasi Manual (tanpa .deb)

### Prasyarat

```bash
sudo apt install python3 python3-gi gir1.2-gtk-3.0 policykit-1
```

### Jalankan langsung

```bash
git clone https://github.com/orchivillando/uclean.git
cd uclean
python3 uclean.py
```

---

## 🔨 Build .deb Sendiri

```bash
git clone https://github.com/orchivillando/uclean.git
cd uclean
bash build_deb.sh
# Output: dist/uclean_1.0.0_all.deb
```

---

## 🔒 Keamanan

Operasi yang membutuhkan `sudo` (apt, snap, journalctl) menggunakan **pkexec** (PolicyKit) sehingga password diminta lewat dialog GUI yang aman — bukan terminal.

---

## 📋 Requirements

- Ubuntu 20.04+ / Debian 11+
- Python 3.6+
- GTK 3.0 (`python3-gi`, `gir1.2-gtk-3.0`)
- PolicyKit (`policykit-1`) untuk operasi sudo

---

## 📄 Lisensi

MIT License © 2026 [Grizenzio Orchivillando](https://github.com/orchivillando)
