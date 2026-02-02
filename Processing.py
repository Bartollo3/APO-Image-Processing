class Processing:
    def linear_stretch(self):
        img = self.ensure_grayscale(self.original_image)
        min_val = np.min(img)
        max_val = np.max(img)
        stretched = ((img - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        new_win = ImageWindow(self.master, stretched)
        new_win.title(f"Rozciąganie - {self.title()}")

    def linear_stretch_clip(self):
        img = self.ensure_grayscale(self.original_image)
        flat = img.flatten()
        low = np.percentile(flat, 5)
        high = np.percentile(flat, 95)
        clipped = np.clip(img, low, high)
        stretched = ((clipped - low) / (high - low) * 255).astype(np.uint8)
        new_win = ImageWindow(self.master, stretched)
        new_win.title(f"Rozciąganie z przesyceniem - {self.title()}")

    def histogram_stretch_dialog(self):
        if self.original_image is None:
            messagebox.showerror("Błąd", "Brak załadowanego obrazu")
            return

        def on_ok():
            try:
                p1 = int(p1_e.get());
                p2 = int(p2_e.get())
                q1 = int(q1_e.get());
                q2 = int(q2_e.get())
            except ValueError:
                messagebox.showerror("Błąd", "Wprowadź liczby całkowite 0-255")
                return
            dialog.destroy()
            self.histogram_stretch_apply(p1, p2, q1, q2)

        dialog = tk.Toplevel(self)
        dialog.title("Rozciąganie histogramu (zakres p1-p2 -> q1-q2)")
        tk.Label(dialog, text="p1:").grid(row=0, column=0);
        p1_e = tk.Entry(dialog);
        p1_e.insert(0, "0");
        p1_e.grid(row=0, column=1)
        tk.Label(dialog, text="p2:").grid(row=1, column=0);
        p2_e = tk.Entry(dialog);
        p2_e.insert(0, "255");
        p2_e.grid(row=1, column=1)
        tk.Label(dialog, text="q1:").grid(row=2, column=0);
        q1_e = tk.Entry(dialog);
        q1_e.insert(0, "0");
        q1_e.grid(row=2, column=1)
        tk.Label(dialog, text="q2:").grid(row=3, column=0);
        q2_e = tk.Entry(dialog);
        q2_e.insert(0, "255");
        q2_e.grid(row=3, column=1)
        tk.Button(dialog, text="OK", command=on_ok).grid(row=4, column=0, pady=6)
        tk.Button(dialog, text="Anuluj", command=dialog.destroy).grid(row=4, column=1, pady=6)
        dialog.transient(self);
        dialog.grab_set();
        dialog.focus_set()

    def histogram_stretch_apply(self, p1, p2, q1, q2):
        img = self.ensure_grayscale(self.original_image)
        if img is None:
            messagebox.showerror("Błąd", "Nie można przetworzyć obrazu")
            return
        p1 = max(0, min(255, p1));
        p2 = max(0, min(255, p2))
        q1 = max(0, min(255, q1));
        q2 = max(0, min(255, q2))
        if p2 == p1:
            messagebox.showerror("Błąd", "p2 musi być różne od p1")
            return
        src = img.astype(np.float32)
        clipped = np.clip(src, p1, p2)
        stretched = (clipped - p1) / (p2 - p1) * (q2 - q1) + q1
        res = np.clip(stretched, 0, 255).astype(np.uint8)
        ImageWindow(self.master, res).title(f"Rozciąganie {p1}-{p2} -> {q1}-{q2} - {self.title()}")

    def equalize_lut(self):
        img = self.ensure_grayscale(self.original_image)
        equalized = cv2.equalizeHist(img)
        new_win = ImageWindow(self.master, equalized)
        new_win.title(f"Equalizacja - {self.title()}")

    def threshold_dialog(self):
        if self.original_image is None:
            messagebox.showerror("Błąd", "Brak załadowanego obrazu")
            return

        def on_confirm():
            try:
                thr = int(entry.get())
                if thr < 0 or thr > 255:
                    messagebox.showerror("Błąd", "Próg musi być w zakresie 0–255")
                    return
                mode = mode_var.get()
                dialog.destroy()
                self.apply_threshold(thr, mode)
            except ValueError:
                messagebox.showerror("Błąd", "Wprowadź liczbę całkowitą")

        dialog = tk.Toplevel(self)
        dialog.title("Progowanie obrazu")
        dialog.geometry("360x160")
        tk.Label(dialog, text="Wprowadź próg (0–255):").pack(pady=(10, 0))
        entry = tk.Entry(dialog)
        entry.insert(0, "128")
        entry.pack(pady=6)

        mode_var = tk.StringVar(value="binary")
        rb_frame = tk.Frame(dialog)
        rb_frame.pack(pady=4, fill="x", padx=8)
        tk.Radiobutton(rb_frame, text="Binarne (piksel > próg -> 255, else 0)",
                       variable=mode_var, value="binary").pack(anchor="w")
        tk.Radiobutton(rb_frame, text="Zachowaj szarość (piksel > próg -> oryginalna wartość, else 0)",
                       variable=mode_var, value="keep").pack(anchor="w")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="OK", width=10, command=on_confirm).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Anuluj", width=10, command=dialog.destroy).pack(side="left")

        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_set()

    def apply_threshold(self, threshold, mode="binary"):
        img = self.ensure_grayscale(self.original_image)
        if img is None:
            messagebox.showerror("Błąd", "Nie można przetworzyć obrazu")
            return

        thr = int(threshold)
        if mode == "binary":
            _, res = cv2.threshold(img, thr, 255, cv2.THRESH_BINARY)
        else:
            mask = img > thr
            res = np.zeros_like(img, dtype=np.uint8)
            res[mask] = img[mask]

        new_win = ImageWindow(self.master, res)
        try:
            if mode == "binary":
                new_win.title(f"Progowanie binarne ({thr}) - {self.title()}")
            else:
                new_win.title(f"Progowanie (zachowaj szarość) ({thr}) - {self.title()}")

    def double_threshold_dialog(self):
        if self.original_image is None:
            messagebox.showerror("Błąd", "Brak załadowanego obrazu")
            return

        def on_ok():
            try:
                t1 = int(t1_e.get());
                t2 = int(t2_e.get())
            except ValueError:
                messagebox.showerror("Błąd", "Wprowadź progi 0-255")
                return
            dialog.destroy()
            self.apply_double_threshold(t1, t2)

        dialog = tk.Toplevel(self)
        dialog.title("Progowanie podwójne")
        tk.Label(dialog, text="Próg 1 (min):").grid(row=0, column=0);
        t1_e = tk.Entry(dialog);
        t1_e.insert(0, "50");
        t1_e.grid(row=0, column=1)
        tk.Label(dialog, text="Próg 2 (max):").grid(row=1, column=0);
        t2_e = tk.Entry(dialog);
        t2_e.insert(0, "200");
        t2_e.grid(row=1, column=1)
        tk.Button(dialog, text="OK", command=on_ok).grid(row=2, column=0, pady=6)
        tk.Button(dialog, text="Anuluj", command=dialog.destroy).grid(row=2, column=1, pady=6)
        dialog.transient(self);
        dialog.grab_set();
        dialog.focus_set()

    def apply_double_threshold(self, t1, t2):
        img = self.ensure_grayscale(self.original_image)
        if img is None:
            return
        lo = min(t1, t2);
        hi = max(t1, t2)
        mask = ((img >= lo) & (img <= hi)).astype(np.uint8) * 255
        ImageWindow(self.master, mask).title(f"Progowanie podwójne {lo}-{hi} - {self.title()}")

    def otsu_threshold(self):
        img = self.ensure_grayscale(self.original_image)
        if img is None:
            messagebox.showerror("Błąd", "Brak obrazu")
            return
        blur = cv2.GaussianBlur(img, (5, 5), 0)
        _, res = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        ImageWindow(self.master, res).title(f"Otsu threshold - {self.title()}")
        print(_)

    def adaptive_threshold_dialog(self):
        if self.original_image is None:
            messagebox.showerror("Błąd", "Brak obrazu")
            return

        def on_ok():
            try:
                block = int(block_e.get())
                C = int(c_e.get())
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowe wartości")
                return
            dialog.destroy()
            method = method_var.get()
            self.apply_adaptive_threshold(block, C, method)

        dialog = tk.Toplevel(self)
        dialog.title("Progowanie adaptacyjne")
        tk.Label(dialog, text="Metoda:").grid(row=0, column=0)
        method_var = tk.StringVar(value="GAUSSIAN")
        tk.OptionMenu(dialog, method_var, "GAUSSIAN", "MEAN").grid(row=0, column=1)
        tk.Label(dialog, text="Rozmiar bloku (odd):").grid(row=1, column=0);
        block_e = tk.Entry(dialog);
        block_e.insert(0, "11");
        block_e.grid(row=1, column=1)
        tk.Label(dialog, text="C (subtrakcja):").grid(row=2, column=0);
        c_e = tk.Entry(dialog);
        c_e.insert(0, "2");
        c_e.grid(row=2, column=1)
        tk.Button(dialog, text="OK", command=on_ok).grid(row=3, column=0, pady=6)
        tk.Button(dialog, text="Anuluj", command=dialog.destroy).grid(row=3, column=1, pady=6)
        dialog.transient(self);
        dialog.grab_set();
        dialog.focus_set()

    def apply_adaptive_threshold(self, blockSize, C, method):
        img = self.ensure_grayscale(self.original_image)
        if img is None:
            return
        if blockSize % 2 == 0:
            blockSize += 1
        if method == "GAUSSIAN":
            m = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        else:
            m = cv2.ADAPTIVE_THRESH_MEAN_C
        res = cv2.adaptiveThreshold(img, 255, m, cv2.THRESH_BINARY, blockSize, C)
        ImageWindow(self.master, res).title(f"Adaptive thresh ({blockSize},{C}) - {self.title()}")

    def hough_dialog(self):
        if self.original_image is None:
            messagebox.showerror("Błąd", "Brak załadowanego obrazu")
            return

        def on_ok():
            method = method_var.get()
            try:
                th1 = int(th1_e.get());
                th2 = int(th2_e.get())
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowe wartości progów")
                return
            dialog.destroy()
            self.hough_apply(method, th1, th2)

        dialog = tk.Toplevel(self)
        dialog.title("Hough - detekcja krawędzi")
        tk.Label(dialog, text="Metoda:").grid(row=0, column=0)
        method_var = tk.StringVar(value="lines")
        tk.OptionMenu(dialog, method_var, "lines", "circles").grid(row=0, column=1)
        tk.Label(dialog, text="Canny th1:").grid(row=1, column=0);
        th1_e = tk.Entry(dialog);
        th1_e.insert(0, "50");
        th1_e.grid(row=1, column=1)
        tk.Label(dialog, text="Canny th2:").grid(row=2, column=0);
        th2_e = tk.Entry(dialog);
        th2_e.insert(0, "150");
        th2_e.grid(row=2, column=1)
        tk.Button(dialog, text="OK", command=on_ok).grid(row=3, column=0, pady=6)
        tk.Button(dialog, text="Anuluj", command=dialog.destroy).grid(row=3, column=1, pady=6)
        dialog.transient(self);
        dialog.grab_set();
        dialog.focus_set()

    def hough_apply(self, method, th1, th2):
        img = self.ensure_grayscale(self.original_image)
        if img is None:
            return
        edges = cv2.Canny(img, th1, th2)
        vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if method == 'lines':
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=30, maxLineGap=10)
            if lines is not None:
                for l in lines:
                    x1, y1, x2, y2 = l[0]
                    cv2.line(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)
        else:
            circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20, param1=th1, param2=30, minRadius=0,
                                       maxRadius=0)
            if circles is not None:
                circles = np.uint16(np.around(circles))
                for c in circles[0, :]:
                    cv2.circle(vis, (c[0], c[1]), c[2], (0, 255, 0), 2)
                    cv2.circle(vis, (c[0], c[1]), 2, (0, 0, 255), 3)
        ImageWindow(self.master, vis).title(f"Hough {method} - {self.title()}")


