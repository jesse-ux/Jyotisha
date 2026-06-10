"""Jaimini Tropical Astrology — Windows GUI

tkinter-based GUI for the Jaimini engine. Packaged as .exe via PyInstaller.
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import io
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jaimini.chart.chart import Chart
from jaimini.engine.time_utils import parse_dms, parse_timezone
from jaimini.core.karakas import karaka_report
from jaimini.core.dashas import format_dasha_table


DEFAULTS = {
    "date": "1949-10-01",
    "time": "15:00:00",
    "tz": "+8",
    "lat": "39.907",
    "lon": "116.397",
    "name": "",
}


class JaiminiApp:
    def __init__(self, root):
        self.root = root
        root.title("Jaimini 回归黄道占星引擎")
        root.geometry("780x720")
        root.resizable(True, True)

        # Input frame
        input_frame = ttk.LabelFrame(root, text="输入参数", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # Row 0: Date, Time, Timezone
        row0 = ttk.Frame(input_frame)
        row0.pack(fill=tk.X, pady=2)
        ttk.Label(row0, text="日期 (YYYY-MM-DD):", width=22).pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value=DEFAULTS["date"])
        ttk.Entry(row0, textvariable=self.date_var, width=14).pack(side=tk.LEFT, padx=2)

        ttk.Label(row0, text="时间 (HH:MM:SS):", width=18).pack(side=tk.LEFT, padx=(15, 0))
        self.time_var = tk.StringVar(value=DEFAULTS["time"])
        ttk.Entry(row0, textvariable=self.time_var, width=12).pack(side=tk.LEFT, padx=2)

        ttk.Label(row0, text="时区:", width=5).pack(side=tk.LEFT, padx=(15, 0))
        self.tz_var = tk.StringVar(value=DEFAULTS["tz"])
        ttk.Entry(row0, textvariable=self.tz_var, width=6).pack(side=tk.LEFT, padx=2)

        # Row 1: Latitude, Longitude, Name
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="纬度 (dec or DMS):", width=22).pack(side=tk.LEFT)
        self.lat_var = tk.StringVar(value=DEFAULTS["lat"])
        ttk.Entry(row1, textvariable=self.lat_var, width=14).pack(side=tk.LEFT, padx=2)

        ttk.Label(row1, text="经度 (dec or DMS):", width=18).pack(side=tk.LEFT, padx=(15, 0))
        self.lon_var = tk.StringVar(value=DEFAULTS["lon"])
        ttk.Entry(row1, textvariable=self.lon_var, width=12).pack(side=tk.LEFT, padx=2)

        ttk.Label(row1, text="名称:", width=5).pack(side=tk.LEFT, padx=(15, 0))
        self.name_var = tk.StringVar(value=DEFAULTS["name"])
        ttk.Entry(row1, textvariable=self.name_var, width=14).pack(side=tk.LEFT, padx=2)

        # Row 2: Options
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, pady=5)
        self.rahu_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text="含 Rahu (8 Karaka)", variable=self.rahu_var).pack(side=tk.LEFT)
        self.dasha_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text="仅 Dasha", variable=self.dasha_var).pack(side=tk.LEFT, padx=(15, 0))
        self.karaka_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text="仅 Karaka", variable=self.karaka_var).pack(side=tk.LEFT, padx=(15, 0))

        # Buttons
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        self.calc_btn = ttk.Button(btn_frame, text="计算星盘", command=self.calculate)
        self.calc_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="复制结果", command=self.copy_result).pack(side=tk.LEFT, padx=5)

        # Output area
        out_frame = ttk.LabelFrame(root, text="计算结果", padding=5)
        out_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.output = scrolledtext.ScrolledText(
            out_frame, wrap=tk.NONE, font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4"
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.insert(tk.END, "就绪。请输入出生数据，点击「计算星盘」。\n")

        # Status bar
        self.status = ttk.Label(root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, padx=10, pady=(0, 5))

    def calculate(self):
        self.calc_btn.config(state=tk.DISABLED)
        self.status.config(text="计算中...")
        self.output.delete(1.0, tk.END)
        self.root.update()

        try:
            dt = datetime.strptime(
                f"{self.date_var.get()} {self.time_var.get()}", "%Y-%m-%d %H:%M:%S"
            )
            lat = parse_dms(self.lat_var.get())
            lon = parse_dms(self.lon_var.get())
            tz = parse_timezone(self.tz_var.get())
            name = self.name_var.get() or None

            chart = Chart(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
                lat, lon, tz, name=name
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                if self.karaka_var.get():
                    karakas = chart.karakas_8 if self.rahu_var.get() else chart.karakas_7
                    print(karaka_report(karakas))
                elif self.dasha_var.get():
                    print(format_dasha_table(chart.chara_dasha, include_antar=True))
                else:
                    print(chart.summary())

            self.output.insert(tk.END, buf.getvalue())
            self.status.config(text="计算完成")

        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.status.config(text=f"错误: {e}")

        self.calc_btn.config(state=tk.NORMAL)

    def clear(self):
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "就绪。\n")
        self.status.config(text="就绪")

    def copy_result(self):
        text = self.output.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status.config(text="结果已复制到剪贴板")


def main():
    root = tk.Tk()
    app = JaiminiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
