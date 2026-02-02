import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
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

    def morphology_dialog(self, op):
        if self.original_image is None:
            messagebox.showerror("Błąd", "Brak załadowanego obrazu")
            return

        def on_ok():
            try:
                it = int(iter_e.get())
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowa liczba iteracji")
                return
            shape = shape_var.get()
            dialog.destroy()
            self.apply_morphology(op, shape, it)

        dialog = tk.Toplevel(self)
        dialog.title(f"Morfologia - {op}")
        tk.Label(dialog, text="Element strukturalny:").grid(row=0, column=0)
        shape_var = tk.StringVar(value="square")
        tk.OptionMenu(dialog, shape_var, "square", "cross").grid(row=0, column=1)
        tk.Label(dialog, text="Liczba iteracji:").grid(row=1, column=0);
        iter_e = tk.Entry(dialog);
        iter_e.insert(0, "1");
        iter_e.grid(row=1, column=1)
        tk.Button(dialog, text="OK", command=on_ok).grid(row=2, column=0, pady=6)
        tk.Button(dialog, text="Anuluj", command=dialog.destroy).grid(row=2, column=1, pady=6)
        dialog.transient(self);
        dialog.grab_set();
        dialog.focus_set()

    def apply_morphology(self, op, shape, iterations=1):
        from ImageWindow import ImageWindow
        img = self.ensure_grayscale(self.original_image)
        if img is None:
            return
        if shape == "square":
            se = np.ones((3, 3), dtype=np.uint8)
        else:
            se = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        if op == 'erode':
            res = cv2.erode(img, se, iterations=iterations)
        elif op == 'dilate':
            res = cv2.dilate(img, se, iterations=iterations)
        elif op == 'open':
            res = cv2.morphologyEx(img, cv2.MORPH_OPEN, se, iterations=iterations)
        else:
            res = cv2.morphologyEx(img, cv2.MORPH_CLOSE, se, iterations=iterations)
        ImageWindow(self.master, res).title(f"Morfologia {op} - {self.title()}")

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
                    try:
                        thresh = int(entry.get())
                        if thresh < 0 or thresh > 255:
                            messagebox.showerror("Błąd", "Próg musi być w zakresie 0–255")
                            return
                        _, marker_img = cv2.threshold(mask, thresh, 255, cv2.THRESH_BINARY)
                        self.apply_reconstruction(mask, marker_img, shape, size)
                        dialog.destroy()
                    except ValueError:
                        messagebox.showerror("Błąd", "Wprowadź liczbę całkowitą")

                dialog = tk.Toplevel(self.master)
                dialog.title("marker progowanie")
                dialog.geometry("200x200")
                tk.Label(dialog, text="Podaj wartość progu:").pack(pady=(10, 0))
                entry = tk.Entry(dialog)
                entry.insert(0, "128")
                entry.pack(pady=6)
                btn_frame = tk.Frame(dialog)
                btn_frame.pack(pady=8)
                tk.Button(btn_frame, text="OK", width=10, command=on_confirm).pack(side="left", padx=6)
                tk.Button(btn_frame, text="Anuluj", width=10, command=dialog.destroy).pack(side="left")
                dialog.transient(self.master)
                dialog.grab_set()
                dialog.focus_set()

            case "erosion":
                def on_confirm():
                    try:
                        it = int(entry.get())
                    except ValueError:
                        messagebox.showerror("Błąd", "Nieprawidłowa liczba iteracji")
                        return
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
        if self.original_image is None:
            messagebox.showerror("Błąd", "Brak załadowanego obrazu")
            return
        img = self.ensure_grayscale(self.original_image)
        if img.max() > 1 and not set(np.unique(img)).issubset({0, 255}):
            _, img_bin = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
        else:
            img_bin = (img > 0).astype(np.uint8) * 255
        skel = self._skeletonize(img_bin)
        ImageWindow(self.master, skel).title(f"Szkielet - {self.title()}")

    def _skeletonize(self, bin_img):
        img = bin_img.copy()
        if img.dtype != np.uint8:
            img = img.astype(np.uint8)
        if img.max() == 1:
            img = img * 255
        skel = np.zeros(img.shape, np.uint8)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        while True:
            eroded = cv2.erode(img, element)
            temp = cv2.dilate(eroded, element)
            temp = cv2.subtract(img, temp)
            skel = cv2.bitwise_or(skel, temp)
            img = eroded.copy()
            if cv2.countNonZero(img) == 0:
                break
        return skel