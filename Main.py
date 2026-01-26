import tkinter as tk
from tkinter import filedialog, messagebox
import ImageWindow

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacja do przetwarzania obrazów")
        self.create_menu()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Wczytaj obraz", command=self.load_image)
        file_menu.add_command(label="Duplikuj obraz", command=self.duplicate_image)
        file_menu.add_separator()
        file_menu.add_command(label="Wyjście", command=self.root.quit)

        menu_bar.add_cascade(label="Plik", menu=file_menu)
        self.root.config(menu=menu_bar)

        self.open_images = []

    def load_image(self):
        filetypes = [("Obrazy", "*.bmp *.tif *.tiff *.png *.jpg *.jpeg")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            win = ImageWindow.ImageWindow(self.root, path)
            self.open_images.append(win)

    def duplicate_image(self):
        if not self.open_images:
            messagebox.showwarning("Brak obrazu", "Najpierw wczytaj obraz.")
            return
        original = self.open_images[-1]
        img_source = original.original_image if getattr(original, "image_path",
                                                        None) is None else original.image_path
        dup_win = ImageWindow(self.root, img_source)
        self.open_images.append(dup_win)


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("400x400")
    root.app = App(root)
    root.mainloop()
