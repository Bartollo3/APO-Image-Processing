import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from unittest import case

import cv2
import numpy as np


class Morphological (tk.Toplevel):
    def __init__(self, master, choice):
        super().__init__(master)
        self.marker_var = None
        self.geometry("360x360")
        self.title("Morphological")
        match choice:
            case "erode":
                self.morphology_dialog('erode')
            case "dilate":
                self.morphology_dialog('dilate')
            case "open":
                self.morphology_dialog('open')
            case "close":
                self.morphology_dialog('close')
            case "reconstruction":
                self.reconstruction_dialog()
            case "skeletonize":
                self.skeletonize_dialog()

    STRUCTURING_ELEMENTS = {
        'krzyz': cv2.MORPH_CROSS,
        'kwadrat': cv2.MORPH_RECT,
        'elipsa': cv2.MORPH_ELLIPSE
    }

    def get_structuring_element(self, shape='rect', size=3):
        #Tworzy element strukturalny do operacji morfologicznych
        if shape not in self.STRUCTURING_ELEMENTS:
            shape = 'rect'

        morph_shape = self.STRUCTURING_ELEMENTS[shape]
        return cv2.getStructuringElement(morph_shape, (size, size))

    def morphology_dialog(self, operation):
        match operation:
            case 'erode':
                pass
            case 'dilate':
                pass
            case 'open':
                pass
            case 'close':
                pass

    def reconstruction_dialog(self):
        def on_confirm():
            self.create_marker(self.marker_var, shape_var, size)
            dialog.destroy()
        dialog = tk.Toplevel(self)
        dialog.title("Rekonstrukcja morfologiczna")
        dialog.geometry("360x360")
        tk.Label(dialog, text="Wybierz rodzaj uzyskania markera \n oraz kształt używany do przeprowadzania dylacji:").pack(pady=(10, 0))
        self.marker_var = tk.StringVar(value="erosion")
        rb_frame = tk.Frame(dialog)
        rb_frame.pack(pady=4, fill="x", padx=8)
        ttk.Radiobutton(rb_frame, text="Marker przez erozję",
                        variable=self.marker_var, value="erosion").pack(anchor="w")
        ttk.Radiobutton(rb_frame, text="Marker przez progowanie",
                        variable=self.marker_var, value="threshold").pack(anchor="w")
        ttk.Radiobutton(rb_frame, text="Marker z gotowego obrazu",
                        variable=self.marker_var, value="custom").pack(anchor="w")
        shape_var = tk.StringVar(value="kwadrat")
        tk.OptionMenu(dialog, shape_var, "kwadrat", "krzyz", "elipsa").pack(pady=5, anchor="center")
        tk.Label(dialog, text="Podaj rozmiar kształtu:").pack(pady=(10, 0))
        entry = tk.Entry(dialog)
        entry.insert(0, "3")
        entry.pack(pady=6)
        size = int(entry.get())
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="OK", width=10, command=on_confirm).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Anuluj", width=10, command=self.destroy).pack(side="left")
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.focus_set()
        self.marker_var.set("erosion")
        dialog.update()

    def create_marker(self, marker, shape, size):
        from ImageWindow import ImageWindow
        img = self.master.ensure_grayscale(self.master.original_image)
        mask = img.copy()
        if img is None:
            return
        match marker.get():
            case "custom":
                path = filedialog.askopenfilename(title="Wybierz obraz do dodania",
                                              filetypes=[("Obrazy", "*.bmp *.tif *.tiff *.png *.jpg *.jpeg")])
                if not path:
                    return
                marker_img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                ok, msg = self.master._check_compat(mask, marker_img)
                if not ok:
                    messagebox.showerror("Błąd", msg)
                    return
                self.apply_reconstruction(mask, marker_img, shape, size)
            case "threshold":
                def on_confirm():
                    _, marker_img = cv2.threshold(mask, thresh, 255, cv2.THRESH_BINARY)
                    self.apply_reconstruction(mask, marker_img, shape, size)
                    dialog.destroy()
                dialog = tk.Toplevel(self.master)
                dialog.title("marker progowanie")
                dialog.geometry("200x200")
                tk.Label(dialog, text="Podaj wartość progu:").pack(pady=(10, 0))
                entry = tk.Entry(dialog)
                entry.insert(0, "128")
                entry.pack(pady=6)
                thresh = int(entry.get())
                btn_frame = tk.Frame(dialog)
                btn_frame.pack(pady=8)
                tk.Button(btn_frame, text="OK", width=10, command=on_confirm).pack(side="left", padx=6)
                tk.Button(btn_frame, text="Anuluj", width=10, command=dialog.destroy).pack(side="left")
                dialog.transient(self.master)
                dialog.grab_set()
                dialog.focus_set()
            case "erosion":
                def on_confirm():
                    kernel = self.get_structuring_element(shape.get(), size)
                    marker_img = cv2.erode(mask, kernel, iterations=it)
                    self.apply_reconstruction(mask, marker_img, shape, size)
                    dialog.destroy()
                dialog = tk.Toplevel(self.master)
                dialog.title("marker erozja")
                dialog.geometry("200x200")
                tk.Label(dialog, text="Podaj ilość iteracji:").pack(pady=(10, 0))
                entry = tk.Entry(dialog)
                entry.insert(0, "1")
                entry.pack(pady=6)
                it = int(entry.get())
                btn_frame = tk.Frame(dialog)
                btn_frame.pack(pady=8)
                tk.Button(btn_frame, text="OK", width=10, command=on_confirm).pack(side="left", padx=6)
                tk.Button(btn_frame, text="Anuluj", width=10, command=dialog.destroy).pack(side="left")
                dialog.transient(self.master)
                dialog.grab_set()
                dialog.focus_set()

    def apply_reconstruction(self, mask, marker_img, shape, size):
        from ImageWindow import ImageWindow
        kernel = self.get_structuring_element(shape.get(), size)
        marker_img = self.master.ensure_grayscale(marker_img)
        marker_img = np.minimum(marker_img, mask)

        prev = marker_img.copy()
        while True:
            dil = cv2.dilate(prev, kernel, iterations=1)
            new = cv2.bitwise_and(dil, mask)
            if np.array_equal(new, prev):
                break
            prev = new

        res = prev
        ImageWindow(self.master, res).title(f"Rekonstrukcja morfologiczna - {self.master.title()}")

    def skeletonize_dialog(self):
        pass