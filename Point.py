import tkinter as tk
from tkinter import messagebox, filedialog

import cv2
import numpy as np


class Point(tk.Toplevel):
    def __init__(self, master, choice):
        super().__init__(master)
        match choice:
            case "apply_negative":
                self.apply_negative()
            case "reduce_gray_levels":
                self.reduce_gray_levels()
            case "add_image_no_clip":
                self.add_images_no_clip()
            case "add_image_clip":
                self.add_images_clip()
            case "mul_no_clip":
                self.scalar_op_dialog("mul", False)
            case "mul":
                self.scalar_op_dialog("mul", True)
            case "add":
                self.scalar_op_dialog("add", True)
            case "sub":
                self.scalar_op_dialog("sub", True)
            case "div":
                self.scalar_op_dialog("div", True)
            case "absdiff":
                self.abs_difference()

    def apply_negative(self):
        from ImageWindow import ImageWindow
        img = self.master.ensure_grayscale(self.master.original_image)
        negative = 255 - img
        new_win = ImageWindow(self.master, negative)
        new_win.title(f"Negacja - {self.title()}")
        self.destroy()

    def reduce_gray_levels(self):
        from ImageWindow import ImageWindow
        def on_confirm():
            try:
                levels = int(entry.get())
                if levels < 2 or levels > 256:
                    messagebox.showerror("Błąd", "Liczba poziomów musi być między 2 a 256")
                    return

                img = self.master.ensure_grayscale(self.master.original_image)

                factor = 256.0 / levels

                reduced = ((img / factor).astype(int) * factor).astype(np.uint8)

                new_win = ImageWindow(self.master, reduced)
                new_win.title(f"Redukcja {levels} poziomów - {self.title()}")
                self.destroy()

            except ValueError:
                messagebox.showerror("Błąd", "Wprowadź poprawną liczbę całkowitą")

        self.title("Redukcja poziomów szarości")
        self.geometry("300x120")

        tk.Label(self, text="Wprowadź liczbę poziomów szarości (2-256):").pack(pady=10)
        entry = tk.Entry(self)
        entry.insert(0, "8")  # Default value
        entry.pack(pady=5)

        tk.Button(self, text="OK", command=on_confirm).pack(pady=10)

        self.transient(self)
        self.grab_set()
        self.focus_set()


    def add_images_no_clip(self):
        from ImageWindow import ImageWindow
        # wczytaj drugi obraz, sprawdź zgodność rozmiaru/typów, sumuj (bez obcinania - z normalizacją)
        path = filedialog.askopenfilename(title="Wybierz obraz do dodania",
                                          filetypes=[("Obrazy", "*.bmp *.tif *.tiff *.png *.jpg *.jpeg")])
        if not path:
            return
        other = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        ok, msg = self.master._check_compat(self.master.original_image, other)
        if not ok:
            messagebox.showerror("Błąd", msg)
            return
        # zapewnij brak przesycenia przez skalowanie zakresów przed dodaniem
        a = self.master.ensure_grayscale(self.master.original_image).astype(np.int32)
        b = self.master.ensure_grayscale(other).astype(np.int32)
        # znormalizuj operand(y) do mniejszego zakresu, aby uniknąć przesycenia:
        a_scaled = ((a / 2)).astype(np.int32)
        b_scaled = ((b / 2)).astype(np.int32)
        summed = (a_scaled + b_scaled).astype(np.int32)
        # dopasuj do 0-255 przez normalizację
        minv, maxv = summed.min(), summed.max()
        if maxv == minv:
            res = np.clip(summed, 0, 255).astype(np.uint8)
        else:
            res = ((summed - minv) / (maxv - minv) * 255).astype(np.uint8)
        new_win = ImageWindow(self.master, res)
        new_win.title(f"Dodawanie (bez obc) - {self.title()}")

    def add_images_clip(self):
        from ImageWindow import ImageWindow
        # dodawanie z obcięciem (saturacja)
        paths = filedialog.askopenfilenames(title="Wybierz 2..5 obrazów do dodania",
                                            filetypes=[("Obrazy", "*.bmp *.tif *.tiff *.png *.jpg *.jpeg")])
        if not paths:
            return
        imgs = [cv2.imread(p, cv2.IMREAD_UNCHANGED) for p in paths]
        all_imgs = [self.master.ensure_grayscale(self.master.original_image)] + [self.master.ensure_grayscale(i) for i in imgs if
                                                                   i is not None]
        # sprawdź rozmiary
        for im in all_imgs:
            if im.shape != all_imgs[0].shape:
                messagebox.showerror("Błąd", "Rozmiary obrazów muszą być zgodne")
                return
        acc = np.zeros_like(all_imgs[0], dtype=np.int32)
        for im in all_imgs:
            acc += im.astype(np.int32)
        acc = np.clip(acc, 0, 255).astype(np.uint8)
        new_win = ImageWindow(self.master, acc)
        new_win.title(f"Dodawanie (z obcięciami) - {self.master.title()}")
        self.destroy()

    def scalar_op_dialog(self, op, clip=True):
        from ImageWindow import ImageWindow
        # mnożenie, dodawanie, odejmowanie lub dzielenie przez wartość całkowitą
        def on_ok():
            try:
                val = int(entry.get())
            except ValueError:
                messagebox.showerror("Błąd", "Wprowadź liczbę całkowitą")
                return
            img = self.master.ensure_grayscale(self.master.original_image).astype(np.int32)
            if op == "mul":
                res = img * val
            elif op == "add":
                res = img + val
            elif op == "sub":
                res = img - val
            else:
                if val == 0:
                    messagebox.showerror("Błąd", "Dzielenie przez zero")
                    return
                res = img // val
            if clip:
                res = np.clip(res, 0, 255).astype(np.uint8)
            else:
                # zastosuj skalowanie aby uniknąć obcięć
                mn, mx = res.min(), res.max()
                if mx == mn:
                    res = np.clip(res, 0, 255).astype(np.uint8)
                else:
                    res = ((res - mn) / (mx - mn) * 255).astype(np.uint8)
            match op:
                case "mul":
                    ImageWindow(self.master, res).title(f"{'Mnożenie'} ({val}) - {self.title()}")
                case "add":
                    ImageWindow(self.master, res).title(f"{'Dodawanie'} ({val}) - {self.title()}")
                case "sub":
                    ImageWindow(self.master, res).title(f"{'Odejmowanie'} ({val}) - {self.title()}")
                case "div":
                    ImageWindow(self.master, res).title(f"{'Dzielenie'} ({val}) - {self.title()}")
            self.destroy()

        self.title("Operacja skalara")
        tk.Label(self, text="Wprowadź liczbę całkowitą:").pack(padx=10, pady=6)
        entry = tk.Entry(self);
        entry.insert(0, "2");
        entry.pack(padx=10, pady=6)
        tk.Button(self, text="OK", command=on_ok).pack(padx=10, pady=6)
        self.transient(self);
        self.grab_set();
        self.focus_set()

    def abs_difference(self):
        from ImageWindow import ImageWindow
        path = filedialog.askopenfilename(title="Wybierz obraz do porównania",
                                          filetypes=[("Obrazy", "*.bmp *.tif *.tiff *.png *.jpg *.jpeg")])
        if not path:
            return
        other = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        ok, msg = self.master._check_compat(self.master.original_image, other)
        if not ok:
            messagebox.showerror("Błąd", msg);
            return
        a = self.master.ensure_grayscale(self.master.original_image)
        b = self.master.ensure_grayscale(other)
        res = cv2.absdiff(a, b)
        ImageWindow(self.master, res).title(f"Różnica bezwzględna - {self.title()}")
        self.destroy()