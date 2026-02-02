class Logical:
    def logical_not(self):
        img = self.ensure_grayscale(self.original_image)
        # jeśli obraz nie binarny, skonwertuj do binary (prog 128)
        if img.max() > 1 and img.max() > 255:
            img = np.clip(img, 0, 255).astype(np.uint8)
        if img.max() > 1:
            _, bin_img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
        else:
            bin_img = (img * 255).astype(np.uint8)
        res = cv2.bitwise_not(bin_img)
        ImageWindow(self.master, res).title(f"NOT - {self.title()}")

    def logical_binary(self, mode):
        path = filedialog.askopenfilename(title=f"Wybierz obraz dla operacji {mode.upper()}",
                                          filetypes=[("Obrazy", "*.bmp *.tif *.tiff *.png *.jpg *.jpeg")])
        if not path:
            return
        other = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        ok, msg = self._check_compat(self.original_image, other)
        if not ok:
            messagebox.showerror("Błąd", msg);
            return
        a = self.ensure_grayscale(self.original_image)
        b = self.ensure_grayscale(other)
        # sprowadź do binarnych masek
        _, a_bin = cv2.threshold(a, 127, 255, cv2.THRESH_BINARY)
        _, b_bin = cv2.threshold(b, 127, 255, cv2.THRESH_BINARY)
        if mode == "and":
            res = cv2.bitwise_and(a_bin, b_bin)
        elif mode == "or":
            res = cv2.bitwise_or(a_bin, b_bin)
        else:
            res = cv2.bitwise_xor(a_bin, b_bin)
        ImageWindow(self.master, res).title(f"{mode.upper()} - {self.title()}")