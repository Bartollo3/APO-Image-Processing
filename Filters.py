import tkinter as tk
from tkinter import messagebox

import cv2
import numpy as np


class Filters(tk.Toplevel):
    def __init__(self, master, choice):
        super().__init__(master)
        match choice:
            case "smoothing_dialog":
                self.smoothing_dialog()
            case "laplace_dialog":
                self.laplace_dialog()
            case "prewitt_dialog":
                self.prewitt_dialog()
            case "sobel_dialog":
                self.sobel_dialog()
            case "median_dialog":
                self.median_dialog()
            case "canny_dialog":
                self.canny_dialog()

    def smoothing_dialog(self):
        from ImageWindow import ImageWindow
        self.title("Wygładzanie")

        left = tk.Frame(self)
        left.grid(row=0, column=0, sticky="ns", padx=8, pady=8)
        right = tk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        tk.Label(left, text="Typ:").pack(anchor="w")
        typ_var = tk.StringVar(value="średnie")
        typ_menu = tk.OptionMenu(left, typ_var, "średnie", "gauss")
        typ_menu.pack(fill="x", pady=(0, 6))

        tk.Label(left, text="Rozmiar maski (odd):").pack(anchor="w")
        size_var = tk.StringVar(value="3")
        size_menu = tk.OptionMenu(left, size_var, "3", "5", "7", "9")
        size_menu.pack(fill="x", pady=(0, 6))

        tk.Label(left, text="Tryb uzupełnienia brzegu:").pack(anchor="w")
        border_var = tk.StringVar(value="BORDER_CONSTANT")
        border_menu = tk.OptionMenu(left, border_var, "BORDER_CONSTANT", "BORDER_REFLECT")
        border_menu.pack(fill="x", pady=(0, 8))

        btn_frame = tk.Frame(left)
        btn_frame.pack(fill="x", pady=(4, 0))

        def do_apply():
            typ = typ_var.get()
            k = int(size_var.get())
            bord = border_var.get()
            border_flag = cv2.BORDER_CONSTANT if bord == "BORDER_CONSTANT" else cv2.BORDER_REFLECT
            img = self.master.ensure_grayscale(self.master.original_image)
            if typ == "średnie":
                kernel = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.float32)
            else:
                g = cv2.getGaussianKernel(k, 0)
                kernel = np.outer(g, g).astype(np.float32)
            res = cv2.filter2D(img, -1, kernel, borderType=border_flag)
            ImageWindow(self.master, res).title(f"Wygładzanie {typ} {k} - {self.master.title()}")
            try:
                self.destroy()
            except Exception:
                pass

        tk.Button(btn_frame, text="Zastosuj", command=do_apply).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Anuluj", command=self.destroy).pack(side="left", padx=4)

        preview_label = tk.Label(right, text="Maski (binary)")
        preview_label.pack()
        previews = tk.Frame(right)
        previews.pack()

        mean_frame = tk.LabelFrame(previews, text="średnie")
        mean_frame.grid(row=0, column=0, padx=6, pady=6)
        gauss_frame = tk.LabelFrame(previews, text="gauss")
        gauss_frame.grid(row=0, column=1, padx=6, pady=6)

        def build_kernels(k):
            k = int(k)
            mean_k = np.ones((k, k), dtype=np.float32) / (k * k)
            g = cv2.getGaussianKernel(k, 0)
            gauss_k = np.outer(g, g).astype(np.float32)
            return mean_k, gauss_k

        def render_matrix(frame, mat):
            # clear
            for w in frame.winfo_children():
                w.destroy()
            m = np.array(mat)
            rows, cols = m.shape
            tol = 1e-9
            for i in range(rows):
                for j in range(cols):
                    v = m[i, j]
                    if v > tol:
                        txt = "1"
                    elif v < -tol:
                        txt = "-"
                    else:
                        txt = "0"
                    lbl = tk.Label(frame, text=txt, width=2, borderwidth=1, relief="solid")
                    lbl.grid(row=i, column=j, padx=1, pady=1)

        def update_previews(*args):
            k = int(size_var.get())
            mean_k, gauss_k = build_kernels(k)
            render_matrix(mean_frame, mean_k)
            render_matrix(gauss_frame, gauss_k)
            if typ_var.get() == "średnie":
                mean_frame.config(bg="#e8f4ff")
                gauss_frame.config(bg=right.cget("bg"))
            else:
                gauss_frame.config(bg="#e8f4ff")
                mean_frame.config(bg=right.cget("bg"))

        update_previews()
        try:
            size_var.trace_add("write", update_previews)
            typ_var.trace_add("write", update_previews)
        except Exception:
            size_var.trace("w", lambda *a: update_previews())
            typ_var.trace("w", lambda *a: update_previews())

        self.transient(self)
        self.grab_set()
        self.focus_set()

    def laplace_dialog(self):
        from ImageWindow import ImageWindow
        masks = [
            np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32),
            np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]], dtype=np.float32),
            np.array([[-1, 2, -1], [2, -4, 2], [-1, 2, -1]], dtype=np.float32)
        ]

        self.title("Wyostrzanie (Laplace)")

        left = tk.Frame(self)
        left.grid(row=0, column=0, sticky="ns", padx=8, pady=8)
        right = tk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        tk.Label(left, text="Wybierz maskę:").pack(anchor="w")
        selected_idx = tk.IntVar(value=0)

        def select_idx(i):
            selected_idx.set(i)
            update_highlight()

        for i, name in enumerate(["mask1", "mask2", "mask3"]):
            tk.Button(left, text=name, command=lambda i=i: select_idx(i)).pack(fill="x", pady=2)

        tk.Label(left, text="Tryb brzegu:").pack(anchor="w", pady=(6, 0))
        border_var = tk.StringVar(value="BORDER_REFLECT")
        tk.OptionMenu(left, border_var, "BORDER_CONSTANT", "BORDER_REFLECT").pack(fill="x", pady=(0, 6))

        btn_frame = tk.Frame(left)
        btn_frame.pack(pady=6)

        def do_apply():
            idx = selected_idx.get()
            bord = border_var.get()
            border_flag = cv2.BORDER_CONSTANT if bord == "BORDER_CONSTANT" else cv2.BORDER_REFLECT
            img = self.master.ensure_grayscale(self.master.original_image)
            lap = cv2.filter2D(img, cv2.CV_32F, masks[idx], borderType=border_flag)
            sharp = cv2.convertScaleAbs(img.astype(np.float32) + lap)
            ImageWindow(self.master, sharp).title(f"maska Laplace {idx + 1} - {self.master.title()}")
            try:
                self.destroy()
            except Exception:
                pass

        tk.Button(btn_frame, text="Zastosuj", command=do_apply).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Zamknij", command=self.destroy).pack(side="left", padx=4)

        preview_label = tk.Label(right, text="Maski (sign)")
        preview_label.pack()
        previews = tk.Frame(right)
        previews.pack()

        frames = []
        for i in range(3):
            lf = tk.LabelFrame(previews, text=f"mask{i + 1}")
            lf.grid(row=0, column=i, padx=6, pady=6)
            frames.append(lf)

        def render_matrix_local(frame, mat):
            for w in frame.winfo_children():
                w.destroy()
            m = np.array(mat)
            rows, cols = m.shape
            tol = 1e-9
            for r in range(rows):
                for c in range(cols):
                    v = m[r, c]
                    if v > tol:
                        txt = "1"
                    elif v < -tol:
                        txt = "-"
                    else:
                        txt = "0"
                    lbl = tk.Label(frame, text=txt, width=2, borderwidth=1, relief="solid")
                    lbl.grid(row=r, column=c, padx=1, pady=1)

        def update_previews():
            for i, f in enumerate(frames):
                render_matrix_local(f, masks[i])
            update_highlight()

        def update_highlight():
            sel = selected_idx.get()
            for i, f in enumerate(frames):
                if i == sel:
                    f.config(bg="#e8f4ff")
                else:
                    f.config(bg=right.cget("bg"))

        update_previews()
        self.transient(self)
        self.grab_set()
        self.focus_set()

    def prewitt_dialog(self):
        from ImageWindow import ImageWindow
        img_base = self.master.ensure_grayscale(self.master.original_image).astype(np.float32)
        prewitt_x = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float32)
        prewitt_y = prewitt_x.T
        kernels = [
            prewitt_x, -prewitt_x, prewitt_y, -prewitt_y,
            np.array([[-1, -1, 0], [-1, 0, 1], [0, 1, 1]], dtype=np.float32),
            -np.array([[-1, -1, 0], [-1, 0, 1], [0, 1, 1]], dtype=np.float32),
            np.array([[0, 1, 1], [-1, 0, 1], [-1, -1, 0]], dtype=np.float32),
            -np.array([[0, 1, 1], [-1, 0, 1], [-1, -1, 0]], dtype=np.float32)
        ]

        self.title("Prewitt - wybierz kierunek (1..8)")

        left = tk.Frame(self)
        left.grid(row=0, column=0, sticky="ns", padx=8, pady=8)
        right = tk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        tk.Label(left, text="Wybierz kierunek (1..8):").pack(anchor="w")
        selected_idx = tk.IntVar(value=0)

        def select_dir(i):
            selected_idx.set(i)
            update_highlight()

        for i in range(8):
            tk.Button(left, text=f"Kierunek {i + 1}", command=lambda i=i: select_dir(i)).pack(fill="x", pady=1)

        tk.Label(left, text="Tryb brzegu:").pack(anchor="w", pady=(6, 0))
        border_var = tk.StringVar(value="BORDER_REFLECT")
        tk.OptionMenu(left, border_var, "BORDER_CONSTANT", "BORDER_REFLECT").pack(fill="x", pady=(0, 6))

        btn_frame = tk.Frame(left)
        btn_frame.pack(pady=6)

        def do_apply():
            idx = selected_idx.get()
            bord = border_var.get()
            border_flag = cv2.BORDER_REFLECT if bord == "BORDER_REFLECT" else cv2.BORDER_CONSTANT
            ker = kernels[idx]
            res = cv2.filter2D(img_base, cv2.CV_32F, ker, borderType=border_flag)
            res = cv2.convertScaleAbs(np.abs(res))
            ImageWindow(self.master, res).title(f"Prewitt {idx + 1} - {self.master.title()}")
            try:
                self.destroy()
            except Exception:
                pass

        tk.Button(btn_frame, text="Zastosuj", command=do_apply).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Zamknij", command=self.destroy).pack(side="left", padx=4)

        preview_label = tk.Label(right, text="Maski (sign)")
        preview_label.pack()
        previews = tk.Frame(right)
        previews.pack()

        frames = []
        for i in range(8):
            lf = tk.LabelFrame(previews, text=f"k{i + 1}")
            lf.grid(row=i // 4, column=i % 4, padx=6, pady=6)
            frames.append(lf)

        def render_matrix_local(frame, mat):
            for w in frame.winfo_children():
                w.destroy()
            m = np.array(mat)
            rows, cols = m.shape
            tol = 1e-9
            for r in range(rows):
                for c in range(cols):
                    v = m[r, c]
                    if v > tol:
                        txt = "1"
                    elif v < -tol:
                        txt = "-"
                    else:
                        txt = "0"
                    lbl = tk.Label(frame, text=txt, width=2, borderwidth=1, relief="solid")
                    lbl.grid(row=r, column=c, padx=1, pady=1)

        def update_previews():
            for i, f in enumerate(frames):
                render_matrix_local(f, kernels[i])
            update_highlight()

        def update_highlight():
            sel = selected_idx.get()
            for i, f in enumerate(frames):
                if i == sel:
                    f.config(bg="#e8f4ff")
                else:
                    f.config(bg=right.cget("bg"))

        update_previews()
        self.transient(self)
        self.grab_set()
        self.focus_set()

    def sobel_dialog(self):
        from ImageWindow import ImageWindow
        def apply(bord):
            img = self.master.ensure_grayscale(self.master.original_image)
            border_flag = cv2.BORDER_REFLECT if bord == "BORDER_REFLECT" else cv2.BORDER_CONSTANT
            gx = cv2.Sobel(img, cv2.CV_16S, 1, 0, ksize=3, borderType=border_flag)
            gy = cv2.Sobel(img, cv2.CV_16S, 0, 1, ksize=3, borderType=border_flag)
            mag = cv2.magnitude(gx.astype(np.float32), gy.astype(np.float32))
            res = cv2.convertScaleAbs(mag)
            ImageWindow(self.master, res).title(f"Sobel magnitude - {self.master.title()}")
            self.destroy()

        self.title("Sobel - detekcja krawędzi")
        tk.Label(self, text="Tryb brzegu:").pack()
        border_var = tk.StringVar(value="BORDER_REFLECT")
        tk.OptionMenu(self, border_var, "BORDER_CONSTANT", "BORDER_REFLECT").pack()
        tk.Button(self, text="OK", command=lambda: apply(border_var.get())).pack(pady=6)
        self.transient(self)
        self.grab_set()
        self.focus_set()

    def median_dialog(self):
        from ImageWindow import ImageWindow
        def apply():
            k = int(size_var.get())
            bord = border_var.get()
            border_flag = cv2.BORDER_REFLECT if bord == "BORDER_REFLECT" else cv2.BORDER_CONSTANT
            img = self.master.ensure_grayscale(self.master.original_image)
            res = cv2.medianBlur(img, k)
            ImageWindow(self.master, res).title(f"Medianowy {k} - {self.master.title()}")
            self.destroy()

        self.title("Filtr medianowy")
        tk.Label(self, text="Rozmiar maski:").pack()
        size_var = tk.StringVar(value="3")
        tk.OptionMenu(self, size_var, "3", "5", "7", "9").pack()
        tk.Label(self, text="Tryb brzegu (informacyjny):").pack()
        border_var = tk.StringVar(value="BORDER_REFLECT")
        tk.OptionMenu(self, border_var, "BORDER_CONSTANT", "BORDER_REFLECT").pack()
        tk.Button(self, text="OK", command=apply).pack(pady=6)
        self.transient(self)
        self.grab_set()
        self.focus_set()

    def canny_dialog(self):
        from ImageWindow import ImageWindow
        def apply():
            try:
                t1 = int(t1_entry.get());
                t2 = int(t2_entry.get())
            except ValueError:
                messagebox.showerror("Błąd", "Wprowadź liczby całkowite")
                return
            img = self.master.ensure_grayscale(self.master.original_image)
            edges = cv2.Canny(img, t1, t2)
            ImageWindow(self.master, edges).title(f"Canny {t1},{t2} - {self.master.title()}")
            self.destroy()

        self.title("Canny")
        tk.Label(self, text="Threshold1:").pack()
        t1_entry = tk.Entry(self)
        t1_entry.insert(0, "100")
        t1_entry.pack()
        tk.Label(self, text="Threshold2:").pack()
        t2_entry = tk.Entry(self)
        t2_entry.insert(0, "200")
        t2_entry.pack()
        tk.Button(self, text="OK", command=apply).pack(pady=6)
        self.transient(self)
        self.grab_set()
        self.focus_set()

    def show_mask_matrix(self, mask, title="Maska binarna"):
        m = np.array(mask)
        if m.ndim == 1:
            m = np.atleast_2d(m)
        rows, cols = m.shape

        win = tk.Toplevel(self)
        win.title(title)

        frame = tk.Frame(win)
        frame.pack(padx=8, pady=8)

        tol = 1e-9
        for i in range(rows):
            for j in range(cols):
                v = m[i, j]
                if v > tol:
                    txt = "1"
                elif v < -tol:
                    txt = "-"
                else:
                    txt = "0"
                lbl = tk.Label(frame, text=txt, width=3, borderwidth=1, relief="solid", bg="white")
                lbl.grid(row=i, column=j, padx=1, pady=1)

        btn = tk.Button(win, text="Zamknij", command=win.destroy)
        btn.pack(pady=(6, 8))
        win.transient(self)
        win.grab_set()
        win.focus_set()