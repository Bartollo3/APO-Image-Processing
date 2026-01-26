import tkinter as tk
import numpy as np
import os
import cv2
from PIL import ImageTk, Image, ImageOps

def cv2_to_tk(image):
    if image is None:
        return None
    if len(image.shape) == 3 and image.shape[2] == 3:
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
    else:
        pil_img = Image.fromarray(image)
    return ImageTk.PhotoImage(pil_img)

class ImageWindow(tk.Toplevel):
    def __init__(self, master, image_source):
        super().__init__(master)
        if isinstance(image_source, np.ndarray):
            self.original_image = image_source.copy()
            self.display_image = self.original_image.copy()
            self.title("Processed Image")
            self.image_path = None
        else:
            self.title(os.path.basename(image_source))
            self.original_image = cv2.imread(image_source, cv2.IMREAD_UNCHANGED)
            if self.original_image is None:
                raise ValueError(f"Could not load image: {image_source}")
            self.display_image = self.original_image.copy()
            self.image_path = image_source
        self.tk_image = None
        self.image_label = tk.Label(self)
        self.image_label.pack(expand=True, fill=tk.BOTH)
        if not hasattr(self, "image_path"):
            self.image_path = None
        self.display_mode = "original"
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.create_menu()
        # Wyświetl obraz natychmiast
        self.update_image()
        # Dopasowuj tylko później (np. przy zmianie okna)
        self.bind("<Configure>", self.on_resize)
        try:
            root = self.master
            app = getattr(root, "app", None)
            if app is not None and hasattr(app, "open_images"):
                app.open_images.append(self)
            elif hasattr(root, "open_images"):
                root.open_images.append(self)
        except Exception:
            pass

    def on_resize(self, event=None):
        if self.display_mode == "fit_to_window":
            if hasattr(self, "_resize_after_id"):
                self.after_cancel(self._resize_after_id)
            self._resize_after_id = self.after(200, self.update_image)

    def create_menu(self):
        menu = tk.Menu(self)

        # Menu Plik
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Zapisz obraz jako", command=self.save_image)
        file_menu.add_command(label="Duplikuj obraz", command=self.duplicate_image)
        file_menu.add_separator()
        file_menu.add_command(label="Zamknij", command=self.destroy)
        menu.add_cascade(label="Plik", menu=file_menu)

        self.config(menu=menu)

    def save_image(self):
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG", "*.png"),
                                                       ("JPEG", "*.jpg"),
                                                       ("BMP", "*.bmp"),
                                                       ("TIFF", "*.tif")])
        if path:
            cv2.imwrite(path, self.display_image)

    def duplicate_image(self):
        img_source = self.original_image if getattr(self, "image_path", None) is None else self.image_path
        new_win = ImageWindow(self.master, img_source)
        if hasattr(self.master, "open_images"):
            self.master.open_images.append(new_win)
        else:
            try:
                app = getattr(self.master, "app", None)
                if app is not None and hasattr(app, "open_images"):
                    app.open_images.append(new_win)
            except Exception:
                pass

    def update_image(self, event=None):
        if self.display_mode == "original":
            img = self.original_image.copy()
        else:
            if self.display_mode == "fullscreen":
                target_width = self.winfo_screenwidth()
                target_height = self.winfo_screenheight()
            elif self.display_mode == "fit_to_window":
                target_width = max(100, self.image_label.winfo_width())
                target_height = max(100, self.image_label.winfo_height())

            current_height, current_width = self.original_image.shape[:2]
            ratio = min(target_width / current_width, target_height / current_height)
            new_size = (int(current_width * ratio), int(current_height * ratio))
            img = cv2.resize(self.original_image, new_size, interpolation=cv2.INTER_LANCZOS4)

        self.display_image = img
        self.tk_image = cv2_to_tk(img)
        self.image_label.config(image=self.tk_image)