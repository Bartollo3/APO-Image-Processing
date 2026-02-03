import tkinter as tk
from tkinter import messagebox, ttk
import cv2
import numpy as np

class Analysis(tk.Toplevel):
    def __init__(self, master, choice):
        super().__init__(master)
        if choice == "histogram":
            self.show_histogram_stats()
        else:
            self.show_lut()

    def show_lut(self):
        lut = self.generate_lut()
        LUTWindow(self, lut)

    def generate_lut(self):
        img = self.master.original_image
        # If single-channel image -> L
        if img.ndim == 2:
            hist = cv2.calcHist([img], [0], None, [256], [0, 256]).astype(int).flatten().tolist()
            return {"L": hist}

        if img.ndim == 3 and img.shape[2] >= 3:
            b = img[:, :, 0]
            g = img[:, :, 1]
            r = img[:, :, 2]
            try:
                if np.array_equal(b, g) and np.array_equal(g, r):
                    hist = cv2.calcHist([b], [0], None, [256], [0, 256]).astype(int).flatten().tolist()
                    return {"L": hist}
            except Exception:
                pass

        # Default: color image histogram per channel (B,G,R)
        b_hist = cv2.calcHist([img], [0], None, [256], [0, 256]).astype(int).flatten().tolist()
        g_hist = cv2.calcHist([img], [1], None, [256], [0, 256]).astype(int).flatten().tolist()
        r_hist = cv2.calcHist([img], [2], None, [256], [0, 256]).astype(int).flatten().tolist()
        return {"R": r_hist, "G": g_hist, "B": b_hist}


    def show_histogram_stats(self, log_scale=False):
        from ImageWindow import ImageWindow
        if self.master.original_image is None:
            messagebox.showerror("Błąd", "Brak załadowanego obrazu")
            return

        img = self.master.original_image
        if img.size == 0:
            messagebox.showerror("Błąd", "Obraz pusty")
            return
        
        pixel_count = img.shape[0] * img.shape[1]
        self.title("Histogram i statystyki")

        tk.Label(self, text=f"Liczba pikseli: {pixel_count}", font=("Arial", 11, "italic")).pack(pady=(8, 0))

        if img.ndim == 2:
            channels = [("Skala szarości", img, "black")]
        else:
            ch_count = img.shape[2] if img.ndim == 3 else 1
            if ch_count >= 3:
                b = img[:, :, 0]
                g = img[:, :, 1]
                r = img[:, :, 2]
                try:
                    is_gray = np.array_equal(b, g) and np.array_equal(g, r)
                except Exception:
                    is_gray = False
                if is_gray:
                    channels = [("Skala szarości", b, "black")]
                else:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    channels = [
                        ("Czerwony", img_rgb[:, :, 0], "red"),
                        ("Zielony", img_rgb[:, :, 1], "green"),
                        ("Niebieski", img_rgb[:, :, 2], "blue")
                    ]
            else:
                channels = [("Skala szarości", img[:, :, 0], "black")]

        notebook = ttk.Notebook(self)
        notebook.pack(padx=10, pady=10)

        for name, channel_data, color in channels:
            hist = cv2.calcHist([channel_data], [0], None, [256], [0, 256])
            hist = hist.flatten()
            mean = float(np.mean(channel_data))
            median = float(np.median(channel_data))
            var = float(np.var(channel_data))
            std = float(np.std(channel_data))

            hist_h = 300
            hist_w = 512
            hist_img = np.full((hist_h, hist_w, 3), 255, dtype=np.uint8)

            data = hist.astype(float)
            if log_scale:
                with np.errstate(divide="ignore"):
                    data = np.log1p(data)
            max_val = data.max() if data.max() > 0 else 1.0

            for i in range(256):
                h = int((data[i] / max_val) * (hist_h - 50))
                if color == "black":
                    draw_col = (0, 0, 0)
                elif color == "red":
                    draw_col = (0, 0, 255)
                elif color == "green":
                    draw_col = (0, 255, 0)
                else:  # "blue"
                    draw_col = (255, 0, 0)
                cv2.line(hist_img, (i * 2, hist_h - 30), (i * 2, hist_h - 30 - h),
                         draw_col, 2)

            font = cv2.FONT_HERSHEY_SIMPLEX
            for val in (0, 128, 255):
                x = int(val * hist_w / 256)
                cv2.putText(hist_img, str(val), (x - 10, hist_h - 10),
                            font, 0.5, (0, 0, 0), 1)

            tab = tk.Frame(notebook)
            notebook.add(tab, text=name)

            hist_tk = ImageWindow.cv2_to_tk(hist_img)
            hist_label = tk.Label(tab, image=hist_tk)
            hist_label.image = hist_tk
            hist_label.pack(padx=10, pady=8)

            stats_frame = tk.Frame(tab)
            stats_frame.pack(padx=10, pady=6)
            tk.Label(stats_frame, text=f"Średnia: {mean:.2f}", font=("Arial", 11)).pack(anchor="w")
            tk.Label(stats_frame, text=f"Mediana: {median:.0f}", font=("Arial", 11)).pack(anchor="w")
            tk.Label(stats_frame, text=f"Wariancja: {var:.2f}", font=("Arial", 11)).pack(anchor="w")
            tk.Label(stats_frame, text=f"Odchylenie standardowe: {std:.2f}", font=("Arial", 11)).pack(anchor="w")

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Zamknij", command=self.destroy).pack(side="right", padx=6)

        def reopen_toggled():
            self.destroy()
            self.show_histogram_stats(log_scale=not log_scale)

class LUTWindow(tk.Toplevel):
    def __init__(self, master, lut):
        super().__init__(master)
        self.title("Tablica LUT")

        self.lut = lut
        self.is_grayscale = self.check_grayscale(lut)

        # Informacja o typie obrazu
        info_label = tk.Label(self, text=f"Typ obrazu: {'Skala szarości' if self.is_grayscale else 'Kolorowy'}",
                              font=("Arial", 12, "bold"))
        info_label.pack(pady=5)

        # Zakładki dla kanałów
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.trees = {}

        # Pasek wyszukiwania + reset
        search_frame = tk.Frame(self)
        search_frame.pack(pady=5)

        tk.Label(search_frame, text="Szukaj wartości:").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<Return>", self.search_value)

        reset_btn = tk.Button(search_frame, text="Resetuj", command=self.reset_search)
        reset_btn.pack(side=tk.LEFT, padx=5)

        for channel in lut.keys():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=f"Kanał {channel}")

            tree = ttk.Treeview(frame, columns=("Wartość", "Liczba wystąpień"), show="headings", height=20)
            tree.heading("Wartość", text="Wartość")
            tree.heading("Liczba wystąpień", text="Liczba wystąpień")
            tree.column("Wartość", width=100, anchor="center")
            tree.column("Liczba wystąpień", width=150, anchor="center")
            tree.pack(expand=True, fill=tk.BOTH)

            self.trees[channel] = tree
            self.populate_tree(channel)


    def check_grayscale(self, lut):
        # Return True when LUT represents a grayscale image.
        # Cases:
        # - single L channel ("L")
        # - has R,G,B and all channel histograms are identical
        keys = list(lut.keys())
        if keys == ["L"]:
            return True
        if all(k in lut for k in ("R", "G", "B")):
            r = lut["R"]
            g = lut["G"]
            b = lut["B"]
            try:
                return all(r[i] == g[i] == b[i] for i in range(256))
            except Exception:
                return False
        return False

    def populate_tree(self, channel, filter_value=None):
        tree = self.trees[channel]
        tree.delete(*tree.get_children())
        for i in range(256):
            if filter_value is None or i == filter_value:
                tree.insert("", "end", values=(i, self.lut[channel][i]))

    def reset_search(self):
        self.search_entry.delete(0, tk.END)
        for channel in self.lut.keys():
            self.populate_tree(channel)

    def search_value(self, event=None):
        try:
            value = int(self.search_entry.get())
            if 0 <= value <= 255:
                for channel in self.lut.keys():
                    self.populate_tree(channel, filter_value=value)
            else:
                messagebox.showwarning("Błąd", "Wartość musi być z zakresu 0–255.")
        except ValueError:
            messagebox.showwarning("Błąd", "Wprowadź liczbę całkowitą.")