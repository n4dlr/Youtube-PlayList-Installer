#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube Ultra Downloader v2.1 — düzəldilmiş, təmizlənmiş və build_gui optimallaşdırılmış versiya.
"""

import os
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import queue
import json
import re
import time
import datetime
import shutil

# winsound yalnız Windows üçün
if platform.system().lower() == "windows":
    try:
        import winsound
    except Exception:
        winsound = None
else:
    winsound = None

APP_TITLE = "YouTube Ultra Downloader v2.1"
LOG_FILE = os.path.join(os.getcwd(), "ytdownloader_log.txt")

PCT_RE = re.compile(
    r"(?P<pct>\d{1,3}(?:\.\d+)?)%\s+of\s+(?P<total>\d+(?:\.\d+)?)(?P<unit>KiB|MiB|GiB|KB|MB|GB)",
    re.IGNORECASE,
)
PCT_APPROX_RE = re.compile(
    r"(?P<pct>\d{1,3}(?:\.\d+)?)%\s+of\s+~?(?P<total>\d+(?:\.\d+)?)(?P<unit>KiB|MiB|GiB|KB|MB|GB)",
    re.IGNORECASE,
)
PCT_ALT_RE = re.compile(r"download\s+(?P<pct>\d{1,3}(?:\.\d+)?)%", re.IGNORECASE)


def human_to_mb(value: float, unit: str) -> float:
    unit = unit.lower()
    v = float(value)
    if unit in ("kib", "kb"):
        return v / 1024.0
    if unit in ("mib", "mb"):
        return v
    if unit in ("gib", "gb"):
        return v * 1024.0
    return v


def play_sound_notification():
    try:
        if winsound:
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        else:
            print("\a")
    except Exception:
        pass


def append_log(text: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {text}\n")
    except Exception:
        pass


def yt_dlp_yoxla_ve_endir():
    system = platform.system().lower()
    exe_name = "yt-dlp.exe" if system == "windows" else "yt-dlp"
    exe_path = os.path.join(os.getcwd(), exe_name)
    if os.path.exists(exe_path):
        return exe_path
    try:
        import urllib.request

        if system == "windows":
            url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        else:
            url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
        urllib.request.urlretrieve(url, exe_path)
        if system != "windows":
            os.chmod(exe_path, 0o755)
        return exe_path
    except Exception as e:
        append_log(f"yt-dlp endirilə bilmədi: {e}")
        print("yt-dlp endirilə bilmədi:", e)
        return None


# ---------------- Main Class ----------------
class UltraDownloader:
    def __init__(self):
        # yt-dlp yoxla / endir
        self.yt_dlp = yt_dlp_yoxla_ve_endir()
        if not self.yt_dlp:
            try:
                root_tmp = tk.Tk()
                root_tmp.withdraw()
                messagebox.showerror(
                    "yt-dlp yoxlanışı",
                    "yt-dlp tapılmadı və endirilə bilmədi.\n\nZəhmət olmasa internet bağlantınızı yoxlayın və yt-dlp sənədini proqram qovluğuna qoyun.",
                )
                root_tmp.destroy()
            except Exception:
                print("yt-dlp tapılmadı və endirilə bilmədi.")
            return

        # iş üçün struktur
        self.q = queue.Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.clear()
        self.threads = []
        self.video_rows = {}
        self.video_info = {}
        self.lock = threading.Lock()
        self.total_videos = 0

        # GUI
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("880x720")
        self.root.minsize(800, 600)

        self.setup_style()
        self.build_gui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(250, self.update_ui)
        append_log("Program başladıldı.")
        self.root.mainloop()

    def setup_style(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.theme = tk.StringVar(value="light")
        self.light_bg = "#f7f7f7"
        self.light_fg = "#000000"
        self.dark_bg = "#2b2b2b"
        self.dark_fg = "#eaeaea"

    def apply_theme(self):
        t = self.theme.get()
        bg, fg = (self.dark_bg, self.dark_fg) if t == "dark" else (self.light_bg, self.light_fg)
        try:
            self.root.configure(bg=bg)
        except Exception:
            pass
        for w in self.root.winfo_children():
            try:
                w.configure(background=bg, foreground=fg)
            except Exception:
                pass
        try:
            self.style.configure("mystyle.Treeview", background=bg, fieldbackground=bg, foreground=fg)
            self.tree.configure(style="mystyle.Treeview")
        except Exception:
            pass

    # ---------------- GUI ----------------
    def build_gui(self):
        frm_top = ttk.Frame(self.root)
        frm_top.pack(fill="x", padx=10, pady=8)

        ttk.Label(frm_top, text="🔗 Playlist və ya Video link:").pack(anchor="w")

        # link + paste
        link_row = ttk.Frame(frm_top)
        link_row.pack(fill="x", pady=4)

        self.link_var = tk.StringVar()
        self.entry_link = ttk.Entry(link_row, textvariable=self.link_var, width=95)
        self.entry_link.pack(side="left", padx=(0, 6), fill="x", expand=True)

        # store paste button to be able to enable/disable later
        self.btn_paste = ttk.Button(link_row, text="📋 Paste", command=self.paste_clipboard)
        self.btn_paste.pack(side="left", padx=2)

        # options row
        opts = ttk.Frame(frm_top)
        opts.pack(fill="x", pady=6)

        # format
        fmt_frame = ttk.LabelFrame(opts, text="Format")
        fmt_frame.pack(side="left", padx=6)
        self.format_var = tk.StringVar(value="mp4")
        for f in ("mp4", "mp3", "wav"):
            ttk.Radiobutton(fmt_frame, text=f.upper(), variable=self.format_var, value=f).pack(side="left", padx=6)

        # threads
        thr_frame = ttk.LabelFrame(opts, text="Parallel (1..50)")
        thr_frame.pack(side="left", padx=6)
        self.threads_var = tk.IntVar(value=8)
        ttk.Entry(thr_frame, textvariable=self.threads_var, width=6, justify="center").pack(padx=6, pady=4)

        # output folder
        out_frame = ttk.Frame(opts)
        out_frame.pack(side="left", padx=6)
        ttk.Label(out_frame, text="Əlavə qovluq:").pack(anchor="w")
        self.output_var = tk.StringVar(value=os.getcwd())
        ofrow = ttk.Frame(out_frame)
        ofrow.pack()
        ttk.Entry(ofrow, textvariable=self.output_var, width=40).pack(side="left", padx=(0, 6))
        ttk.Button(ofrow, text="Seç", command=self.choose_output).pack(side="left")

        # control buttons
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill="x", padx=10, pady=6)

        self.btn_start = ttk.Button(ctrl_frame, text="🚀 Start Downloads", command=self.start_all)
        self.btn_start.pack(side="left", padx=6)

        self.btn_pause = ttk.Button(ctrl_frame, text="⏸ Pause", command=self.toggle_pause, state="disabled")
        self.btn_pause.pack(side="left", padx=6)

        self.btn_stop = ttk.Button(ctrl_frame, text="⛔ Stop All", command=self.stop_all, state="disabled")
        self.btn_stop.pack(side="left", padx=6)

        ttk.Button(ctrl_frame, text="🗒 Open Log", command=self.open_log).pack(side="right", padx=6)
        ttk.Checkbutton(
            ctrl_frame, text="Dark Mode", variable=self.theme, onvalue="dark", offvalue="light", command=self.apply_theme
        ).pack(side="right", padx=6)

        # treeview for videos
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill="both", padx=10, pady=6, expand=True)

        columns = ("title", "status", "percent", "mb")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        for c, w in zip(columns, (420, 140, 80, 120)):
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=8)
        ttk.Label(bottom, text="Ümumi:").pack(side="left")

        self.total_progress = ttk.Progressbar(bottom, orient="horizontal", length=420, mode="determinate")
        self.total_progress.pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="Hazır")
        ttk.Label(bottom, textvariable=self.status_var).pack(side="left", padx=8)

        self.apply_theme()

    def paste_clipboard(self):
        try:
            self.link_var.set(self.root.clipboard_get())
        except Exception:
            messagebox.showwarning("Clipboard", "Clipboard-dan məlumat alınmadı.")

    def choose_output(self):
        d = filedialog.askdirectory(initialdir=self.output_var.get())
        if d:
            self.output_var.set(d)

    def open_log(self):
        try:
            if os.path.exists(LOG_FILE):
                if platform.system().lower() == "windows":
                    os.startfile(LOG_FILE)
                else:
                    subprocess.Popen(["xdg-open", LOG_FILE])
            else:
                messagebox.showinfo("Log", "Hələ log faylı yaradılmayıb.")
        except Exception as e:
            messagebox.showerror("Xəta", f"Log açılmadı:\n{e}")

    # ---------------- Playlist hazırlığı ----------------
    def prepare_playlist_thread(self):
        threading.Thread(target=self.prepare_playlist, daemon=True).start()

    def prepare_playlist(self):
        url = self.link_var.get().strip()
        if not url:
            return
        self.clear_tree()
        self.status_var.set("Playlist oxunur...")
        try:
            out = subprocess.check_output([self.yt_dlp, "-J", "--flat-playlist", url], text=True, stderr=subprocess.STDOUT)
            info = json.loads(out)
            entries = info.get("entries") if isinstance(info, dict) else None

            if not entries:
                self.total_videos = 1
                self.tree.insert("", "end", iid="v1", values=("Tək video", "Hazır", "0%", "0.0"))
                self.video_rows[1] = "v1"
                self.video_info[1] = {"url": url, "title": info.get("title", "Video"), "status": "queued", "percent": 0.0, "mb": 0.0}
                self.q.put((1, url))
            else:
                self.total_videos = len(entries)
                for i, e in enumerate(entries, 1):
                    vid = e.get("id")
                    vurl = f"https://www.youtube.com/watch?v={vid}"
                    title = e.get("title", f"Video {i}")
                    iid = f"v{i}"
                    self.tree.insert("", "end", iid=iid, values=(f"#{i} - {title}", "Gözləyir", "0%", "0.0"))
                    self.video_rows[i] = iid
                    self.video_info[i] = {"url": vurl, "title": title, "status": "queued", "percent": 0.0, "mb": 0.0}
                    self.q.put((i, vurl))

            self.status_var.set(f"{self.total_videos} video sıraya alındı.")
            append_log(f"{self.total_videos} video aşkarlandı.")
        except subprocess.CalledProcessError as e:
            try:
                out = e.output if hasattr(e, "output") else str(e)
            except Exception:
                out = str(e)
            messagebox.showerror("yt-dlp Xətası", f"yt-dlp playlisti oxuya bilmədi!\n\nKomanda çıxışı:\n{out}")
            append_log(f"yt-dlp xətası: {out}")
            self.status_var.set("Xəta")
        except json.JSONDecodeError as e:
            messagebox.showerror("Xəta", f"yt-dlp-dən gələn nəticə pars edilə bilmədi:\n{e}")
            append_log(f"JSON parse xətası: {e}")
            self.status_var.set("Xəta")
        except Exception as e:
            messagebox.showerror("Xəta", f"Playlist oxunmadı:\n{e}")
            append_log(f"Playlist hazırlama xətası: {e}")
            self.status_var.set("Xəta")

    # ---------------- Yükləmə ----------------
    def start_all(self):
        # əgər siyahı hələ yoxdursa — sinxron şəkildə hazırlayırıq
        if self.total_videos == 0:
            self.prepare_playlist()
            if self.total_videos == 0:
                messagebox.showerror("Xəta", "Heç bir video tapılmadı. Zəhmət olmasa linki yoxla.")
                return

        if self.q.empty():
            messagebox.showwarning("Xəbərdarlıq", "Yükləmək üçün video yoxdur.")
            return

        try:
            max_threads = max(1, min(50, int(self.threads_var.get())))
        except Exception:
            max_threads = 4
        self.max_threads = max_threads

        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="normal")
        self.btn_stop.config(state="normal")
        self.pause_event.clear()

        append_log(f"Yükləmələr başladı. Paralel: {self.max_threads}, format: {self.format_var.get()}")
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.worker_loop, daemon=True)
            t.start()
            self.threads.append(t)

    def stop_all(self):
        self.stop_event.set()
        # təmizləyirik queue-ni
        with self.q.mutex:
            self.q.queue.clear()
        self.status_var.set("Dayandırıldı")
        self.btn_pause.config(state="disabled")
        self.btn_stop.config(state="disabled")
        self.btn_start.config(state="normal")
        append_log("Bütün yükləmələr dayandırıldı.")

    def toggle_pause(self):
        if not self.pause_event.is_set():
            self.pause_event.set()
            self.btn_pause.config(text="▶ Resume")
            self.status_var.set("Dayandırıldı (pause)")
        else:
            self.pause_event.clear()
            self.btn_pause.config(text="⏸ Pause")
            self.status_var.set("Davam edir")

    def worker_loop(self):
        while not self.stop_event.is_set():
            try:
                idx, url = self.q.get(timeout=1)
            except queue.Empty:
                break
            try:
                self.run_download(idx, url)
            except Exception as e:
                append_log(f"Error download idx {idx}: {e}")
                with self.lock:
                    if idx in self.video_info:
                        self.video_info[idx]["status"] = "error"
                        self.tree.set(self.video_rows.get(idx, ""), "status", "Xəta")
            finally:
                self.q.task_done()
        append_log("Worker thread çıxır.")

    def run_download(self, idx, video_url):
        # pause halında gözləyirik
        while self.pause_event.is_set():
            time.sleep(0.2)

        fmt = self.format_var.get()

        # əgər playlistdən gəlirsə, fayl adının əvvəlində sıra nömrəsi olsun
        if idx and self.total_videos > 1:
            output_template = os.path.join(self.output_var.get(), f"#{idx:02d} - %(title)s.%(ext)s")
        else:
            output_template = os.path.join(self.output_var.get(), "%(title)s.%(ext)s")

        if fmt == "mp4":
    args = [
        "-f",
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "--merge-output-format",
        "mp4",
        "--audio-format",
        "mp3",
        "--embed-metadata",
        "--embed-thumbnail",
        "--prefer-ffmpeg",
        "--compat-options",
        "no-keep-subs",
    ]
        else:
            args = ["-f", "bestaudio/best", "--extract-audio", "--audio-format", fmt]

        cmd = [self.yt_dlp, *args, "-o", output_template, "--newline", video_url]

        with self.lock:
            if idx in self.video_info:
                self.video_info[idx]["status"] = "downloading"
            self.tree.set(self.video_rows.get(idx, ""), "status", "Yüklənir")
            self.tree.set(self.video_rows.get(idx, ""), "percent", "0%")
            self.tree.set(self.video_rows.get(idx, ""), "mb", "0.0")
        append_log(f"Başladı idx={idx} url={video_url}")

        proc = None
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
            if not proc.stdout:
                raise RuntimeError("yt-dlp stdout açılmadı")

            for line in proc.stdout:
                # pause halında loopu saxla
                while self.pause_event.is_set():
                    time.sleep(0.2)

                m = PCT_RE.search(line) or PCT_APPROX_RE.search(line) or PCT_ALT_RE.search(line)
                if m:
                    try:
                        pct = float(m.group("pct"))
                    except Exception:
                        pct = 0.0

                    downloaded_mb = None
                    try:
                        if m.re is PCT_ALT_RE:
                            downloaded_mb = None
                        else:
                            total_mb = human_to_mb(float(m.group("total")), m.group("unit"))
                            downloaded_mb = total_mb * (pct / 100.0)
                    except Exception:
                        downloaded_mb = None

                    with self.lock:
                        if idx in self.video_info:
                            self.video_info[idx]["percent"] = pct
                            if downloaded_mb is not None:
                                self.video_info[idx]["mb"] = downloaded_mb
                                self.tree.set(self.video_rows.get(idx, ""), "mb", f"{downloaded_mb:.2f}")
                        self.tree.set(self.video_rows.get(idx, ""), "percent", f"{pct:.1f}%")

            return_code = proc.wait()
            with self.lock:
                if return_code == 0:
                    if idx in self.video_info:
                        self.video_info[idx]["status"] = "done"
                    self.tree.set(self.video_rows.get(idx, ""), "status", "✅ Bitdi")
                    self.tree.set(self.video_rows.get(idx, ""), "percent", "100%")
                else:
                    if idx in self.video_info:
                        self.video_info[idx]["status"] = "error"
                    self.tree.set(self.video_rows.get(idx, ""), "status", "Xəta")
            append_log(f"Bitdi idx={idx} url={video_url} rc={return_code}")
            if return_code == 0:
                play_sound_notification()
        except Exception as e:
            try:
                if proc:
                    proc.kill()
            except Exception:
                pass
            with self.lock:
                if idx in self.video_info:
                    self.video_info[idx]["status"] = "error"
                self.tree.set(self.video_rows.get(idx, ""), "status", "Xəta")
            append_log(f"Exception download idx={idx}: {e}")
        finally:
            try:
                if proc and proc.stdout:
                    proc.stdout.close()
            except Exception:
                pass

    # ---------------- UI yenilənməsi ----------------
    def update_ui(self):
        try:
            done_count = sum(1 for v in self.video_info.values() if v.get("status") == "done")
            self.total_progress["maximum"] = max(1, self.total_videos)
            self.total_progress["value"] = done_count
            self.status_var.set(f"{done_count}/{self.total_videos} tamamlandı")
        except Exception:
            pass
        self.root.after(500, self.update_ui)

    def clear_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.video_rows.clear()
        self.video_info.clear()
        with self.q.mutex:
            self.q.queue.clear()
        self.total_videos = 0
        try:
            self.total_progress["value"] = 0
        except Exception:
            pass
        append_log("Tree və queue təmizləndi.")

    def on_close(self):
        if messagebox.askokcancel("Exit", "Programdan çıxmaq istəyirsiniz?"):
            self.stop_event.set()
            try:
                self.root.destroy()
            except Exception:
                pass


def auto_setup():
    system = platform.system().lower()

    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        print("[AUTO-SETUP] ffmpeg tapılmadı. Qurulur...")
        try:
            if system in ("linux", "darwin"):
                subprocess.run(["sudo", "apt", "update"], check=False)
                subprocess.run(["sudo", "apt", "install", "ffmpeg", "-y"], check=False)
            print("[AUTO-SETUP] ffmpeg quraşdırılmağa cəhd olundu!")
        except Exception as e:
            print("[AUTO-SETUP] ffmpeg quraşdırıla bilmədi:", e)
    else:
        print("[AUTO-SETUP] ffmpeg artıq var:", ffmpeg_path)

    ytdlp_path = shutil.which("yt-dlp")
    if not ytdlp_path:
        print("[AUTO-SETUP] yt-dlp tapılmadı. Qurulur...")
        try:
            if system in ("linux", "darwin"):
                subprocess.run(["sudo", "apt", "install", "yt-dlp", "-y"], check=False)
            print("[AUTO-SETUP] yt-dlp quraşdırılmağa cəhd olundu!")
        except Exception as e:
            print("[AUTO-SETUP] yt-dlp quraşdırıla bilmədi:", e)
    else:
        print("[AUTO-SETUP] yt-dlp artıq mövcuddur:", ytdlp_path)


if __name__ == "__main__":
    auto_setup()
    UltraDownloader() 