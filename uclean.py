#!/usr/bin/env python3
"""
UClean — Ubuntu System Cleaner
Bersihkan sistem Ubuntu dengan satu klik.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango

import subprocess
import os
import shutil
import threading
import re


CSS = b"""
* { font-family: Ubuntu, Cantarell, sans-serif; }

.header-box {
    background-color: #E65100;
    padding: 16px 20px;
}
.app-title {
    color: white;
    font-size: 22px;
    font-weight: bold;
}
.app-sub {
    color: #FFE0B2;
    font-size: 11px;
}
.item-row {
    background-color: white;
    border-radius: 6px;
    padding: 4px 8px;
    margin: 2px 0;
    border: 1px solid #e0e0e0;
}
.item-name {
    font-size: 13px;
    font-weight: bold;
    color: #212121;
}
.item-desc {
    font-size: 11px;
    color: #757575;
}
.size-label {
    color: #E65100;
    font-weight: bold;
    font-size: 13px;
}
.size-clean {
    color: #4CAF50;
    font-size: 13px;
}
.total-row {
    padding: 4px 8px;
}
.btn-scan {
    background-color: #1565C0;
    color: white;
    font-weight: bold;
    border-radius: 5px;
    padding: 8px 18px;
    border: none;
    font-size: 13px;
}
.btn-scan:hover { background-color: #0D47A1; }
.btn-scan:disabled { background-color: #90A4AE; }

.btn-clean {
    background-color: #E65100;
    color: white;
    font-weight: bold;
    border-radius: 5px;
    padding: 8px 20px;
    border: none;
    font-size: 14px;
}
.btn-clean:hover { background-color: #BF360C; }
.btn-clean:disabled { background-color: #BCAAA4; }

.statusbar {
    background-color: #EEEEEE;
    padding: 4px 12px;
    font-size: 12px;
    color: #424242;
}
progressbar trough { min-height: 6px; }
progressbar progress { background-color: #E65100; }
"""

ITEMS = [
    {
        "id": "apt_cache",
        "name": "APT Cache",
        "desc": "Cache paket apt yang sudah diunduh",
        "sudo": True,
        "icon": "📦",
    },
    {
        "id": "autoremove",
        "name": "Paket Tidak Terpakai",
        "desc": "Dependensi orphan yang tidak dibutuhkan",
        "sudo": True,
        "icon": "🗑️",
    },
    {
        "id": "journal",
        "name": "Journal Log Lama",
        "desc": "Log sistem lebih dari 7 hari",
        "sudo": True,
        "icon": "📋",
    },
    {
        "id": "trash",
        "name": "Trash / Tempat Sampah",
        "desc": "File yang sudah dihapus ke tempat sampah",
        "sudo": False,
        "icon": "🗑️",
    },
    {
        "id": "thumbnails",
        "name": "Thumbnail Cache",
        "desc": "Cache gambar preview file manager",
        "sudo": False,
        "icon": "🖼️",
    },
    {
        "id": "snap_old",
        "name": "Snap Versi Lama",
        "desc": "Versi snap yang sudah dinonaktifkan",
        "sudo": True,
        "icon": "📦",
    },
]


def fmt_size(b):
    if b <= 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}" if unit != "B" else f"{int(b)} B"
        b /= 1024
    return f"{b:.2f} TB"


def dir_size(path):
    try:
        r = subprocess.run(["du", "-sb", path], capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            return int(r.stdout.split()[0])
    except Exception:
        pass
    return 0


class UCleanApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="UClean")
        self.set_default_size(560, 520)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # State
        self.sizes = [0] * len(ITEMS)
        self.scanning = False
        self.cleaning = False

        self._build_ui()
        GLib.idle_add(self.do_scan)

    # ─── UI Builder ────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hdr.get_style_context().add_class("header-box")
        t = Gtk.Label(label="🧹 UClean")
        t.get_style_context().add_class("app-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label="Ubuntu System Cleaner — Bersihkan sistem dengan satu klik")
        s.get_style_context().add_class("app-sub")
        s.set_halign(Gtk.Align.START)
        hdr.pack_start(t, False, False, 0)
        hdr.pack_start(s, False, False, 0)
        root.pack_start(hdr, False, False, 0)

        # Items list
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(6)

        self.checkboxes = []
        self.size_labels = []

        for i, item in enumerate(ITEMS):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.get_style_context().add_class("item-row")

            cb = Gtk.CheckButton()
            cb.set_active(True)
            cb.set_sensitive(False)
            self.checkboxes.append(cb)

            lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            nl = Gtk.Label()
            nl.set_markup(f"<b>{item['icon']} {item['name']}</b>")
            nl.set_halign(Gtk.Align.START)
            dl = Gtk.Label(label=item["desc"])
            dl.set_halign(Gtk.Align.START)
            dl.get_style_context().add_class("item-desc")
            lbox.pack_start(nl, False, False, 0)
            lbox.pack_start(dl, False, False, 0)

            sl = Gtk.Label(label="—")
            sl.get_style_context().add_class("size-label")
            sl.set_width_chars(10)
            sl.set_xalign(1.0)
            self.size_labels.append(sl)

            row.pack_start(cb, False, False, 4)
            row.pack_start(lbox, True, True, 2)
            row.pack_end(sl, False, False, 8)
            content.pack_start(row, False, False, 3)

        # Separator + Total
        sep = Gtk.Separator()
        content.pack_start(sep, False, False, 8)

        total_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        total_row.get_style_context().add_class("total-row")
        tl = Gtk.Label()
        tl.set_markup("<b>Total yang dapat dibebaskan</b>")
        tl.set_halign(Gtk.Align.START)
        self.total_lbl = Gtk.Label(label="—")
        self.total_lbl.get_style_context().add_class("size-label")
        self.total_lbl.set_xalign(1.0)
        total_row.pack_start(tl, True, True, 0)
        total_row.pack_end(self.total_lbl, False, False, 8)
        content.pack_start(total_row, False, False, 0)

        root.pack_start(content, True, True, 0)

        # Progress bar
        self.pbar = Gtk.ProgressBar()
        self.pbar.set_margin_start(12)
        self.pbar.set_margin_end(12)
        self.pbar.set_margin_bottom(4)
        self.pbar.set_no_show_all(True)
        root.pack_start(self.pbar, False, False, 0)

        # Status bar
        self.status = Gtk.Label(label="Memindai sistem…")
        self.status.get_style_context().add_class("statusbar")
        self.status.set_halign(Gtk.Align.START)
        self.status.set_margin_start(12)
        self.status.set_margin_bottom(2)
        root.pack_start(self.status, False, False, 0)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_start(12)
        btn_box.set_margin_end(12)
        btn_box.set_margin_top(6)
        btn_box.set_margin_bottom(14)

        self.btn_scan = Gtk.Button(label="🔍  Pindai Ulang")
        self.btn_scan.get_style_context().add_class("btn-scan")
        self.btn_scan.connect("clicked", lambda _: self.do_scan())
        self.btn_scan.set_sensitive(False)

        self.btn_clean = Gtk.Button(label="🧹  Bersihkan Sekarang")
        self.btn_clean.get_style_context().add_class("btn-clean")
        self.btn_clean.connect("clicked", self.do_clean)
        self.btn_clean.set_sensitive(False)

        btn_box.pack_start(self.btn_scan, False, False, 0)
        btn_box.pack_end(self.btn_clean, False, False, 0)
        root.pack_start(btn_box, False, False, 0)

    # ─── Scanning ──────────────────────────────────────────────────────────────

    def do_scan(self):
        if self.scanning or self.cleaning:
            return
        self.scanning = True
        self.btn_scan.set_sensitive(False)
        self.btn_clean.set_sensitive(False)
        for cb in self.checkboxes:
            cb.set_sensitive(False)
        for sl in self.size_labels:
            sl.set_text("…")
        self.total_lbl.set_text("—")
        self.status.set_text("Memindai sistem…")
        self.pbar.show()
        self._pulse_id = GLib.timeout_add(120, self._pulse)
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _pulse(self):
        if self.scanning:
            self.pbar.pulse()
            return True
        return False

    def _scan_thread(self):
        results = []

        # APT cache
        s = dir_size("/var/cache/apt/archives/")
        results.append(s)
        GLib.idle_add(self._set_size, 0, s)

        # Autoremove — dry-run
        s2 = 0
        try:
            r = subprocess.run(
                ["apt-get", "--dry-run", "autoremove", "--purge"],
                capture_output=True, text=True, timeout=20
            )
            m = re.search(r"After this operation,\s+([\d,]+)\s*([kMGT]?B)", r.stdout)
            if m:
                val = int(m.group(1).replace(",", ""))
                mult = {"B": 1, "kB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}
                s2 = val * mult.get(m.group(2), 1)
        except Exception:
            pass
        results.append(s2)
        GLib.idle_add(self._set_size, 1, s2)

        # Journal logs
        j = dir_size("/var/log/journal") + dir_size("/run/log/journal")
        results.append(j)
        GLib.idle_add(self._set_size, 2, j)

        # Trash
        t = dir_size(os.path.expanduser("~/.local/share/Trash"))
        results.append(t)
        GLib.idle_add(self._set_size, 3, t)

        # Thumbnails
        th = dir_size(os.path.expanduser("~/.cache/thumbnails"))
        results.append(th)
        GLib.idle_add(self._set_size, 4, th)

        # Snap disabled versions
        snap_count = 0
        try:
            r = subprocess.run(["snap", "list", "--all"], capture_output=True, text=True, timeout=10)
            snap_count = sum(1 for l in r.stdout.splitlines() if "disabled" in l)
        except Exception:
            pass
        results.append(snap_count)
        GLib.idle_add(self._set_snap, 5, snap_count)

        self.sizes = results
        total = sum(results[:5])  # snap size unknown, skip
        GLib.idle_add(self._scan_done, total)

    def _set_size(self, idx, size):
        if size > 0:
            self.size_labels[idx].set_text(fmt_size(size))
            self.size_labels[idx].get_style_context().remove_class("size-clean")
            self.size_labels[idx].get_style_context().add_class("size-label")
        else:
            self.size_labels[idx].set_text("✓ Bersih")
            self.size_labels[idx].get_style_context().remove_class("size-label")
            self.size_labels[idx].get_style_context().add_class("size-clean")

    def _set_snap(self, idx, count):
        if count > 0:
            self.size_labels[idx].set_text(f"{count} versi")
            self.size_labels[idx].get_style_context().remove_class("size-clean")
            self.size_labels[idx].get_style_context().add_class("size-label")
        else:
            self.size_labels[idx].set_text("✓ Bersih")
            self.size_labels[idx].get_style_context().remove_class("size-label")
            self.size_labels[idx].get_style_context().add_class("size-clean")

    def _scan_done(self, total):
        self.scanning = False
        if hasattr(self, "_pulse_id"):
            GLib.source_remove(self._pulse_id)
        self.pbar.hide()
        self.total_lbl.set_text(fmt_size(total))
        for cb in self.checkboxes:
            cb.set_sensitive(True)
        self.btn_scan.set_sensitive(True)
        self.btn_clean.set_sensitive(True)
        if total > 0:
            self.status.set_text(f"✅  Pemindaian selesai — {fmt_size(total)} dapat dibebaskan")
        else:
            self.status.set_text("✅  Sistem sudah bersih!")

    # ─── Cleaning ──────────────────────────────────────────────────────────────

    def do_clean(self, _widget):
        if self.scanning or self.cleaning:
            return

        selected = [i for i, cb in enumerate(self.checkboxes) if cb.get_active()]
        if not selected:
            self.status.set_text("⚠️  Pilih minimal satu item")
            return

        needs_sudo = any(ITEMS[i]["sudo"] for i in selected)
        if needs_sudo:
            dlg = Gtk.MessageDialog(
                transient_for=self,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Bersihkan sistem sekarang?",
            )
            dlg.format_secondary_text(
                "Beberapa operasi memerlukan hak administrator.\n"
                "Anda akan diminta memasukkan password sudo."
            )
            resp = dlg.run()
            dlg.destroy()
            if resp != Gtk.ResponseType.YES:
                return

        self.cleaning = True
        self.btn_clean.set_sensitive(False)
        self.btn_scan.set_sensitive(False)
        self.pbar.set_fraction(0)
        self.pbar.show()

        threading.Thread(target=self._clean_thread, args=(selected,), daemon=True).start()

    def _run_sudo(self, cmd):
        try:
            r = subprocess.run(
                ["pkexec", "bash", "-c", cmd],
                capture_output=True, text=True, timeout=180
            )
            return r.returncode == 0
        except Exception:
            return False

    def _clean_thread(self, selected):
        n = len(selected)
        freed = 0

        for step, idx in enumerate(selected):
            name = ITEMS[idx]["name"]
            GLib.idle_add(self.status.set_text, f"🧹  Membersihkan {name}…")
            GLib.idle_add(self.pbar.set_fraction, (step + 0.5) / n)

            ok = False
            if idx == 0:
                ok = self._run_sudo("apt-get clean -y && apt-get autoclean -y")
                if ok:
                    freed += self.sizes[0]

            elif idx == 1:
                ok = self._run_sudo("DEBIAN_FRONTEND=noninteractive apt-get autoremove --purge -y")
                if ok:
                    freed += self.sizes[1]

            elif idx == 2:
                ok = self._run_sudo("journalctl --vacuum-time=7d")
                if ok:
                    freed += self.sizes[2]

            elif idx == 3:
                try:
                    trash = os.path.expanduser("~/.local/share/Trash")
                    for sub in ("files", "info"):
                        p = os.path.join(trash, sub)
                        if os.path.exists(p):
                            shutil.rmtree(p)
                            os.makedirs(p)
                    freed += self.sizes[3]
                    ok = True
                except Exception:
                    ok = False

            elif idx == 4:
                try:
                    thumb = os.path.expanduser("~/.cache/thumbnails")
                    if os.path.exists(thumb):
                        shutil.rmtree(thumb)
                        os.makedirs(thumb)
                    freed += self.sizes[4]
                    ok = True
                except Exception:
                    ok = False

            elif idx == 5:
                cmd = (
                    "snap list --all | awk '/disabled/{print $1, $3}' | "
                    "while read name rev; do snap remove \"$name\" --revision=\"$rev\"; done"
                )
                ok = self._run_sudo(cmd)

            GLib.idle_add(self.pbar.set_fraction, (step + 1) / n)

        GLib.idle_add(self._clean_done, freed)

    def _clean_done(self, freed):
        self.cleaning = False
        self.pbar.set_fraction(1.0)

        dlg = Gtk.MessageDialog(
            transient_for=self,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="✅  Pembersihan Selesai!",
        )
        dlg.format_secondary_text(
            f"Berhasil membebaskan sekitar {fmt_size(freed)} dari disk Anda.\n\n"
            "Sistem Anda sekarang lebih bersih 🎉"
        )
        dlg.run()
        dlg.destroy()

        self.status.set_text(f"✅  Selesai — ~{fmt_size(freed)} dibebaskan")
        GLib.idle_add(self.do_scan)


def main():
    app = UCleanApp()
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
