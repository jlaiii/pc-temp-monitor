import tkinter as tk
import subprocess
import sys
import os
import time
import ctypes
from datetime import datetime

try:
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
except:
    pass

try:
    import psutil
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "-q"],
                   capture_output=True, timeout=30)
    import psutil

def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

if not _is_admin():
    script = os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}"', None, 1
    )
    sys.exit(0)

LHM_PATH = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "LHM", "LibreHardwareMonitorLib.dll")
LHM_OK = False
LHM_COMPUTER = None

def _init_lhm():
    global LHM_OK, LHM_COMPUTER
    if not os.path.isfile(LHM_PATH):
        return False
    try:
        import clr
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "pythonnet", "-q"],
                       capture_output=True, timeout=30)
        import clr
    try:
        sys.path.append(os.path.dirname(LHM_PATH))
        clr.AddReference("LibreHardwareMonitorLib")
        from LibreHardwareMonitor import Hardware
        c = Hardware.Computer()
        c.IsCpuEnabled = True
        c.IsGpuEnabled = True
        c.IsMotherboardEnabled = True
        c.IsStorageEnabled = True
        c.IsControllerEnabled = True
        c.Open()
        time.sleep(0.5)
        LHM_COMPUTER = c
        LHM_OK = True
        return True
    except:
        return False

def _lhm_cpu_temp():
    if not LHM_OK or LHM_COMPUTER is None:
        return None
    try:
        for hw in LHM_COMPUTER.Hardware:
            htype = str(hw.HardwareType)
            if "cpu" not in htype.lower():
                continue
            hw.Update()
            for s in hw.Sensors:
                if str(s.SensorType) == "Temperature" and s.Value is not None:
                    val = float(s.Value)
                    if val > 0:
                        return round(val, 1)
        return None
    except:
        return None

BG = "#0f0f1a"
BG2 = "#1a1a2e"
BG3 = "#25253d"
FG = "#e0e0f0"
FG2 = "#9090b0"
GREEN = "#4ade80"
YELLOW = "#fbbf24"
RED = "#f87171"
BLUE = "#60a5fa"
PURPLE = "#a78bfa"

class TempMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Temp Monitor")
        self.on_top = True
        try:
            self.root.attributes('-topmost', self.on_top)
        except:
            pass

        w, h = 370, 400
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.running = True
        self.cpu_temp = None
        self.gpu_temp = None
        self.cpu_usage = 0
        self.gpu_usage = 0
        self.ram_usage = 0
        self.gpu_name = ""
        self.gpu_available = False
        self.cpu_available = False
        self.cpu_source = ""
        self.gpu_source = ""
        self.use_fahrenheit = False
        self.transparent = False
        self.cpu_min = None
        self.cpu_max = None
        self.gpu_min = None
        self.gpu_max = None

        _init_lhm()
        self.setup_ui()
        self.detect_hardware()
        self.root.after(500, self.update)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def setup_ui(self):
        self.title_frame = tk.Frame(self.root, bg=BG)
        self.title_frame.pack(pady=(8, 2))

        self.title_frame.bind("<Button-1>", self._drag_start)
        self.title_frame.bind("<B1-Motion>", self._drag_move)

        self.title_label = tk.Label(self.title_frame, text="PC Temp Monitor", font=("Segoe UI", 15, "bold"),
                                     bg=BG, fg=FG)
        self.title_label.pack(side="left")

        self.close_btn = tk.Label(self.title_frame, text="\u00D7", font=("Segoe UI", 14, "bold"),
                                   bg=BG, fg=RED, cursor="hand2")
        self.close_btn.pack(side="right", padx=(10, 0))
        self.close_btn.bind("<Button-1>", lambda e: self.on_close())

        subtitle_frame = tk.Frame(self.root, bg=BG)
        subtitle_frame.pack()
        self.subtitle_text = tk.Label(subtitle_frame, text="CPU & GPU temps",
                                        font=("Segoe UI", 8), bg=BG, fg=FG2)
        self.subtitle_text.pack(side="left")

        self.unit_btn = tk.Button(subtitle_frame, text="\u00b0C", font=("Segoe UI", 8, "bold"),
                                   bg=BG3, fg=FG, activebackground=BG2, activeforeground=FG,
                                   relief="flat", padx=6, cursor="hand2", bd=0,
                                   command=self.toggle_unit)
        self.unit_btn.pack(side="left", padx=(6, 0))

        self.pin_btn = tk.Button(subtitle_frame, text="\u25B2 Pin", font=("Segoe UI", 8, "bold"),
                                  bg=BG3, fg=BLUE, activebackground=BG2, activeforeground=BLUE,
                                  relief="flat", padx=6, cursor="hand2", bd=0,
                                  command=self.toggle_pin)
        self.pin_btn.pack(side="left", padx=(3, 0))

        self.reset_btn = tk.Button(subtitle_frame, text="Reset", font=("Segoe UI", 8, "bold"),
                                    bg=BG3, fg=YELLOW, activebackground=BG2, activeforeground=YELLOW,
                                    relief="flat", padx=6, cursor="hand2", bd=0,
                                    command=self.reset_minmax)
        self.reset_btn.pack(side="left", padx=(3, 0))

        self.minimal_btn = tk.Button(subtitle_frame, text="\u25CB Opaque", font=("Segoe UI", 8, "bold"),
                                      bg=BG3, fg=FG2, activebackground=BG2, activeforeground=FG,
                                      relief="flat", padx=6, cursor="hand2", bd=0,
                                      command=self.toggle_minimal)
        self.minimal_btn.pack(side="left", padx=(3, 0))

        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(expand=True, fill="both", padx=12, pady=3)

        self.cpu_card = tk.Frame(self.main, bg=BG2, highlightbackground=BG3, highlightthickness=1)
        self.cpu_card.pack(fill="x", pady=2, ipady=3)

        self.cpu_row1 = tk.Frame(self.cpu_card, bg=BG2)
        self.cpu_row1.pack(fill="x", padx=10, pady=(4, 0))
        tk.Label(self.cpu_row1, text="CPU", font=("Segoe UI", 12, "bold"), bg=BG2, fg=BLUE).pack(side="left")
        self.cpu_usage_label = tk.Label(self.cpu_row1, text="", font=("Segoe UI", 9), bg=BG2, fg=FG2)
        self.cpu_usage_label.pack(side="right")

        self.cpu_temp_label = tk.Label(self.cpu_card, text="-- \u00b0C", font=("Segoe UI", 30, "bold"),
                                        bg=BG2, fg=FG2)
        self.cpu_temp_label.pack(pady=(0, 1))

        self.cpu_minmax_frame = tk.Frame(self.cpu_card, bg=BG2)
        self.cpu_minmax_frame.pack()
        tk.Label(self.cpu_minmax_frame, text="Lo ", font=("Segoe UI", 8), bg=BG2, fg=FG2).pack(side="left")
        self.cpu_min_label = tk.Label(self.cpu_minmax_frame, text="--", font=("Segoe UI", 8, "bold"), bg=BG2, fg=BLUE)
        self.cpu_min_label.pack(side="left")
        tk.Label(self.cpu_minmax_frame, text=" Hi ", font=("Segoe UI", 8), bg=BG2, fg=FG2).pack(side="left")
        self.cpu_max_label = tk.Label(self.cpu_minmax_frame, text="--", font=("Segoe UI", 8, "bold"), bg=BG2, fg=RED)
        self.cpu_max_label.pack(side="left")

        self.cpu_status = tk.Label(self.cpu_card, text="Detecting...", font=("Segoe UI", 8), bg=BG2, fg=FG2)
        self.cpu_status.pack()

        self.gpu_card = tk.Frame(self.main, bg=BG2, highlightbackground=BG3, highlightthickness=1)
        self.gpu_card.pack(fill="x", pady=2, ipady=3)

        self.gpu_row2 = tk.Frame(self.gpu_card, bg=BG2)
        self.gpu_row2.pack(fill="x", padx=10, pady=(4, 0))
        tk.Label(self.gpu_row2, text="GPU", font=("Segoe UI", 12, "bold"), bg=BG2, fg=PURPLE).pack(side="left")
        self.gpu_usage_label = tk.Label(self.gpu_row2, text="", font=("Segoe UI", 9), bg=BG2, fg=FG2)
        self.gpu_usage_label.pack(side="right")

        self.gpu_temp_label = tk.Label(self.gpu_card, text="-- \u00b0C", font=("Segoe UI", 30, "bold"),
                                        bg=BG2, fg=FG2)
        self.gpu_temp_label.pack(pady=(0, 1))

        self.gpu_minmax_frame = tk.Frame(self.gpu_card, bg=BG2)
        self.gpu_minmax_frame.pack()
        tk.Label(self.gpu_minmax_frame, text="Lo ", font=("Segoe UI", 8), bg=BG2, fg=FG2).pack(side="left")
        self.gpu_min_label = tk.Label(self.gpu_minmax_frame, text="--", font=("Segoe UI", 8, "bold"), bg=BG2, fg=PURPLE)
        self.gpu_min_label.pack(side="left")
        tk.Label(self.gpu_minmax_frame, text=" Hi ", font=("Segoe UI", 8), bg=BG2, fg=FG2).pack(side="left")
        self.gpu_max_label = tk.Label(self.gpu_minmax_frame, text="--", font=("Segoe UI", 8, "bold"), bg=BG2, fg=RED)
        self.gpu_max_label.pack(side="left")

        self.gpu_status = tk.Label(self.gpu_card, text="Detecting...", font=("Segoe UI", 8), bg=BG2, fg=FG2)
        self.gpu_status.pack()

        self.ram_card = tk.Frame(self.main, bg=BG2, highlightbackground=BG3, highlightthickness=1)
        self.ram_card.pack(fill="x", pady=2, ipady=2)

        row3 = tk.Frame(self.ram_card, bg=BG2)
        row3.pack(fill="x", padx=10, pady=(3, 0))
        tk.Label(row3, text="RAM", font=("Segoe UI", 10, "bold"), bg=BG2, fg=GREEN).pack(side="left")
        self.ram_usage_label = tk.Label(row3, text="", font=("Segoe UI", 9), bg=BG2, fg=FG2)
        self.ram_usage_label.pack(side="right")

        self.ram_bar_frame = tk.Frame(self.ram_card, bg=BG3, height=6)
        self.ram_bar_frame.pack(fill="x", padx=10, pady=(3, 6))
        self.ram_bar = tk.Frame(self.ram_bar_frame, bg=GREEN, height=10)
        self.ram_bar.place(x=0, y=0, relwidth=0, relheight=1)

        foot_frame = tk.Frame(self.root, bg=BG)
        foot_frame.pack(side="bottom", pady=(0, 6))
        self.footer = tk.Label(foot_frame, text="", font=("Segoe UI", 8), bg=BG, fg=FG2)
        self.footer.pack(side="left")
        self.footer_link = tk.Label(foot_frame, text="made by jlaiii", font=("Segoe UI", 8),
                                     bg=BG, fg=BLUE, cursor="hand2")
        self.footer_link.pack(side="left")
        self.footer_link.bind("<Button-1>", lambda e: self._open_github())
        self.footer_link.bind("<Enter>", lambda e: None)

    def toggle_unit(self):
        self.use_fahrenheit = not self.use_fahrenheit
        self.unit_btn.config(text="\u00b0F" if self.use_fahrenheit else "\u00b0C")

    def toggle_pin(self):
        self.on_top = not self.on_top
        try:
            self.root.attributes('-topmost', self.on_top)
        except:
            pass
        txt = "\u25B2 Pin" if self.on_top else "\u25BC Pin"
        self.pin_btn.config(text=txt, fg=BLUE if self.on_top else FG2)

    def _set_bg_all(self, parent, color):
        try:
            parent.configure(bg=color)
        except:
            pass
        try:
            for child in parent.winfo_children():
                self._set_bg_all(child, color)
        except:
            pass

    def toggle_minimal(self):
        self.transparent = not self.transparent
        if self.transparent:
            self._set_bg_all(self.root, BG2)
            self.cpu_card.configure(highlightbackground=BG2)
            self.gpu_card.configure(highlightbackground=BG2)
            self.ram_card.configure(highlightbackground=BG2)
            for btn in [self.unit_btn, self.pin_btn, self.reset_btn, self.minimal_btn]:
                btn.configure(bg=BG3, fg=FG)
            self.minimal_btn.configure(fg=BLUE)
            self.close_btn.configure(bg="#2a0a0a")
            try:
                self.root.overrideredirect(True)
                self.root.attributes('-transparentcolor', BG2)
            except:
                pass
            self.close_btn.lift()
            self.minimal_btn.config(text="\u25C9 See-Through")
        else:
            try:
                self.root.attributes('-transparentcolor', '')
                self.root.overrideredirect(False)
            except:
                pass
            self.root.configure(bg=BG)
            self.title_frame.configure(bg=BG)
            self.title_label.configure(bg=BG)
            self.close_btn.configure(bg=BG)
            self.subtitle_text.configure(bg=BG)
            self.unit_btn.configure(bg=BG3)
            self.pin_btn.configure(bg=BG3)
            self.reset_btn.configure(bg=BG3)
            self.minimal_btn.configure(bg=BG3, fg=FG2)
            self.minimal_btn.config(text="\u25CB Opaque")
            self.main.configure(bg=BG)
            self.cpu_card.configure(bg=BG2, highlightbackground=BG3)
            self.gpu_card.configure(bg=BG2, highlightbackground=BG3)
            self.ram_card.configure(bg=BG2, highlightbackground=BG3)
            for card in [self.cpu_card, self.gpu_card, self.ram_card]:
                self._set_bg_all(card, BG2)
            for w in [self.footer.master, self.footer, self.footer_link]:
                try: w.configure(bg=BG)
                except: pass

    def reset_minmax(self):
        self.cpu_min = None
        self.cpu_max = None
        self.gpu_min = None
        self.gpu_max = None

    def detect_hardware(self):
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0 and r.stdout.strip():
                self.gpu_available = True
                self.gpu_name = r.stdout.strip().split("\n")[0][:40]
                self.gpu_source = "nvidia-smi"
        except:
            pass

        if LHM_OK:
            try:
                for hw in LHM_COMPUTER.Hardware:
                    htype = str(hw.HardwareType)
                    if "cpu" in htype.lower():
                        self.cpu_available = True
                        self.cpu_source = "LHM"
                        break
            except:
                pass

        if not self.cpu_available:
            try:
                r = subprocess.run(
                    ["powershell", "-Command",
                     "(Get-CimInstance -ClassName Win32_PerfFormattedData_Counters_ThermalZoneInformation).Temperature"],
                    capture_output=True, text=True, timeout=5
                )
                if r.returncode == 0 and r.stdout.strip():
                    self.cpu_available = True
                    self.cpu_source = "WMI"
            except:
                pass

    def get_cpu_temp_wmi(self):
        try:
            r = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance -ClassName Win32_PerfFormattedData_Counters_ThermalZoneInformation).Temperature"],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0 and r.stdout.strip():
                lines = r.stdout.strip().split("\n")
                temps = []
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            k = float(line)
                            temps.append(k - 273.15)
                        except:
                            pass
                if temps:
                    return round(max(temps), 1)
        except:
            pass
        return None

    def get_cpu_temp(self):
        if LHM_OK:
            t = _lhm_cpu_temp()
            if t is not None and t > 1:
                self.cpu_source = "LHM"
                return t
        t = self.get_cpu_temp_wmi()
        if t is not None:
            self.cpu_source = "WMI (ambient)"
            return t
        self.cpu_source = "no sensor"
        return None

    def get_gpu_temp(self):
        if self.gpu_available:
            try:
                r = subprocess.run(
                    ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=3
                )
                if r.returncode == 0 and r.stdout.strip():
                    return int(r.stdout.strip())
            except:
                pass
        return None

    def get_gpu_usage(self):
        if self.gpu_available:
            try:
                r = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=3
                )
                if r.returncode == 0 and r.stdout.strip():
                    val = r.stdout.strip().split("\n")[0]
                    return int(val.replace(" %", ""))
            except:
                pass
        return None

    def to_unit(self, temp_c):
        if temp_c is None:
            return None, "\u00b0C"
        if self.use_fahrenheit:
            return round(temp_c * 9 / 5 + 32), "\u00b0F"
        return round(temp_c), "\u00b0C"

    def set_temp_color(self, label, temp_c, c_thresh, f_thresh):
        if temp_c is None:
            label.config(fg=FG2)
            return
        lo, hi = (f_thresh if self.use_fahrenheit else c_thresh)
        if temp_c < lo:
            label.config(fg=GREEN)
        elif temp_c < hi:
            label.config(fg=YELLOW)
        else:
            label.config(fg=RED)

    def update(self):
        if not self.running:
            return

        try:
            if self.cpu_available:
                self.cpu_usage = psutil.cpu_percent(interval=None)
                self.cpu_temp = self.get_cpu_temp()
                if self.cpu_temp is not None:
                    if self.cpu_min is None or self.cpu_temp < self.cpu_min:
                        self.cpu_min = self.cpu_temp
                    if self.cpu_max is None or self.cpu_temp > self.cpu_max:
                        self.cpu_max = self.cpu_temp
                    val, unit = self.to_unit(self.cpu_temp)
                    self.cpu_temp_label.config(text=f"{val}{unit}")
                    self.set_temp_color(self.cpu_temp_label, self.cpu_temp, (50, 70), (122, 158))
                    min_val, _ = self.to_unit(self.cpu_min)
                    max_val, _ = self.to_unit(self.cpu_max)
                    self.cpu_min_label.config(text=f"{min_val}{unit}")
                    self.cpu_max_label.config(text=f"{max_val}{unit}")
                    self.cpu_usage_label.config(text=f"{self.cpu_usage}%")
                    self.cpu_status.config(text=f"{self.cpu_source}")
                else:
                    self.cpu_temp_label.config(text="N/A")
                    self.cpu_usage_label.config(text="")
                    self.cpu_status.config(text="CPU temp unavailable")
            else:
                self.cpu_temp_label.config(text="N/A")
                self.cpu_usage_label.config(text="")
                self.cpu_status.config(text="No CPU sensor detected")
        except Exception as e:
            self.cpu_status.config(text=f"CPU error: {str(e)[:30]}")

        try:
            if self.gpu_available:
                self.gpu_temp = self.get_gpu_temp()
                self.gpu_usage = self.get_gpu_usage()
                if self.gpu_temp is not None:
                    if self.gpu_min is None or self.gpu_temp < self.gpu_min:
                        self.gpu_min = self.gpu_temp
                    if self.gpu_max is None or self.gpu_temp > self.gpu_max:
                        self.gpu_max = self.gpu_temp
                    val, unit = self.to_unit(self.gpu_temp)
                    self.gpu_temp_label.config(text=f"{val}{unit}")
                    self.set_temp_color(self.gpu_temp_label, self.gpu_temp, (50, 75), (122, 167))
                    min_val, _ = self.to_unit(self.gpu_min)
                    max_val, _ = self.to_unit(self.gpu_max)
                    self.gpu_min_label.config(text=f"{min_val}{unit}")
                    self.gpu_max_label.config(text=f"{max_val}{unit}")
                    usg = f"{self.gpu_usage}%" if self.gpu_usage is not None else ""
                    self.gpu_usage_label.config(text=usg)
                    self.gpu_status.config(text=f"{self.gpu_source} | {self.gpu_name}")
                else:
                    self.gpu_temp_label.config(text="Err")
                    self.gpu_status.config(text="Error reading GPU")
            else:
                self.gpu_temp_label.config(text="--")
                self.gpu_usage_label.config(text="")
                self.gpu_status.config(text="No NVIDIA GPU detected")
        except Exception as e:
            self.gpu_status.config(text=f"GPU error: {str(e)[:30]}")

        try:
            self.ram_usage = psutil.virtual_memory().percent
            self.ram_usage_label.config(text=f"{self.ram_usage}%")
            bar_color = GREEN
            if self.ram_usage > 80:
                bar_color = RED
            elif self.ram_usage > 60:
                bar_color = YELLOW
            self.ram_bar.config(bg=bar_color)
            self.ram_bar.place(x=0, y=0, relwidth=self.ram_usage/100, relheight=1)
        except:
            pass

        now = datetime.now().strftime("%I:%M:%S %p")
        unit = "\u00b0F" if self.use_fahrenheit else "\u00b0C"
        self.footer.config(text=f"{now}  |  {unit}  |  Admin mode  |  ")
        self.root.after(2000, self.update)

    def _open_github(self):
        try:
            subprocess.Popen(["cmd", "/c", "start", "https://github.com/jlaiii"])
        except:
            try:
                import webbrowser
                webbrowser.open("https://github.com/jlaiii")
            except:
                pass

    def _drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def on_close(self):
        self.running = False
        if LHM_COMPUTER is not None:
            try:
                LHM_COMPUTER.Close()
            except:
                pass
        self.root.destroy()


if __name__ == "__main__":
    TempMonitor()
