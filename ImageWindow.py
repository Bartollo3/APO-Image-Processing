import tkinter as tk
from tkinter import filedialog
import numpy as np
import os
import cv2
from PIL import ImageTk, Image, ImageOps
from Analysis import Analysis
from Processing import Processing
from Point import Point
from Logical import Logical
from Filters import Filters
from Morphological import Morphological

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
        #Wyświetl obraz natychmiast
        self.update_image()
        #Dopasowuj tylko później (np. przy zmianie okna)
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

        #Menu Plik
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Zapisz obraz jako", command=self.save_image)
        file_menu.add_command(label="Duplikuj obraz", command=self.duplicate_image)
        file_menu.add_separator()
        file_menu.add_command(label="Zamknij", command=self.destroy)
        menu.add_cascade(label="Plik", menu=file_menu)

        #Menu Widok
        view_menu = tk.Menu(menu, tearoff=0)
        view_menu.add_command(label="Oryginalna rozdzielczość", command=self.show_original_size)
        view_menu.add_command(label="Dopasuj do okna", command=self.fit_to_window)
        view_menu.add_command(label="Pełny ekran", command=self.fullscreen)
        menu.add_cascade(label="Widok", menu=view_menu)

        #Analiza
        lut_menu = tk.Menu(menu, tearoff=0)
        lut_menu.add_command(label="Pokaż tablicę LUT", command=Analysis.show_lut)
        lut_menu.add_command(label="Histogram i statystyki", command=Analysis.show_histogram)
        menu.add_cascade(label="Analiza", menu=lut_menu)

        #Przetwarzanie
        processing_menu = tk.Menu(menu, tearoff=0)
        processing_menu.add_command(label="Rozciąganie bez przesycenia", command=Processing.linear_stretch)
        processing_menu.add_command(label="Rozciąganie z przesyceniem 5%", command=Processing.linear_stretch_clip)
        processing_menu.add_command(label="Rozciąganie (p1-p2 -> q1-q2)", command=Processing.histogram_stretch_dialog)
        processing_menu.add_command(label="Equalizacja LUT", command=Processing.equalize_lut)
        processing_menu.add_command(label="Progowanie (binarne / zachowaj szarość)", command=Processing.threshold_dialog)
        seg_menu = tk.Menu(processing_menu, tearoff=0)
        seg_menu.add_command(label="Progowanie podwójne (dwa progi)", command=Processing.double_threshold_dialog)
        seg_menu.add_command(label="Progowanie Otsu", command=Processing.otsu_threshold)
        seg_menu.add_command(label="Progowanie adaptacyjne", command=Processing.adaptive_threshold_dialog)
        processing_menu.add_cascade(label="Segmentacja", menu=seg_menu)
        processing_menu.add_command(label="Hough - detekcja krawędzi (linie/okręgi)", command=Processing.hough_dialog)
        menu.add_cascade(label="Przetwarzanie obrazu", menu=processing_menu)

        #Menu Operacje punktowe
        point_menu = tk.Menu(menu, tearoff=0)
        point_menu.add_command(label="Negacja", command=Point.apply_negative)
        point_menu.add_command(label="Redukcja poziomów szarości", command=Point.reduce_gray_levels)

        #Wieloargumentowe (dodawanie, mnożenie, dzielenie, różnica bezwzględna)

        menu.add_cascade(label="Operacje punktowe", menu=point_menu)

        #Operacje logiczne
        logic_menu = tk.Menu(menu, tearoff=0)
        logic_menu.add_command(label="NOT (pojedynczy obraz)", command=Logical.logical_not)
        logic_menu.add_command(label="AND (między obrazami)", command=lambda: Logical.logical_operations("and"))
        logic_menu.add_command(label="OR  (między obrazami)", command=lambda: Logical.logical_operations("or"))
        logic_menu.add_command(label="XOR (między obrazami)", command=lambda: Logical.logical_operations("xor"))
        menu.add_cascade(label="Operacje logiczne", menu=logic_menu)

        #Sąsiedztwo / Filtry liniowe / Laplasjan / Prewitt / Sobel / Mediana / Canny
        neigh_menu = tk.Menu(menu, tearoff=0)
        neigh_menu.add_command(label="Wygładzanie (średnie / wagowe / Gaussowskie)", command=Filters.smoothing_dialog)
        neigh_menu.add_command(label="Wyostrzanie (3 maski Laplace'a)", command=Filters.laplace_dialog)
        neigh_menu.add_command(label="Prewitt - detekcja kierunkowa (8 kierunków)", command=Filters.prewitt_dialog)
        neigh_menu.add_command(label="Sobel (dwie prostopadłe maski)", command=Filters.sobel_dialog)
        neigh_menu.add_separator()
        neigh_menu.add_command(label="Filtr medianowy (3x3..9x9)", command=Filters.median_dialog)
        neigh_menu.add_command(label="Canny - detekcja krawędzi", command=Filters.canny_dialog)
        menu.add_cascade(label="Sąsiedztwo / Filtry", menu=neigh_menu)

        #Morfologia
        morph_menu = tk.Menu(menu, tearoff=0)
        morph_menu.add_command(label="Erozja", command=lambda: Morphological.morphology_dialog('erode'))
        morph_menu.add_command(label="Dylacja", command=lambda: Morphological.morphology_dialog('dilate'))
        morph_menu.add_command(label="Otwarcie", command=lambda: Morphological.morphology_dialog('open'))
        morph_menu.add_command(label="Zamknięcie", command=lambda: Morphological.morphology_dialog('close'))
        morph_menu.add_separator()
        morph_menu.add_command(label="Rekonstrukcja morfologiczna", command=Morphological.reconstruction_dialog)
        processing_menu.add_command(label="Szkieletyzacja", command=Morphological.skeletonize_dialog)
        menu.add_cascade(label="Morfologia", menu=morph_menu)

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

    def show_original_size(self):
        self.display_mode = "original"
        self.update_image()

    def fit_to_window(self):
        self.display_mode = "fit_to_window"
        self.update_image()

    def fullscreen(self):
        self.display_mode = "fullscreen"
        self.attributes("-fullscreen", True)
        self.update_image()