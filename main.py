import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import os
import random
import math
from concurrent.futures import ThreadPoolExecutor


class MosaicGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mosaic Montage Generator")

        self.main_image_path = None
        self.small_images_folder = None
        self.target_width = 1000
        self.target_height = 1000

        # GUI Components
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Main Image:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.main_image_button = tk.Button(self.root, text="Choose Image", command=self.choose_main_image)
        self.main_image_button.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.root, text="Small Images Folder:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.small_images_button = tk.Button(self.root, text="Choose Folder", command=self.choose_small_images_folder)
        self.small_images_button.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.root, text="Width:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.width_entry = tk.Entry(self.root)
        self.width_entry.insert(0, str(self.target_width))
        self.width_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(self.root, text="Height:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.height_entry = tk.Entry(self.root)
        self.height_entry.insert(0, str(self.target_height))
        self.height_entry.grid(row=3, column=1, padx=10, pady=5)

        self.generate_button = tk.Button(self.root, text="Generate Mosaic", command=self.generate_mosaic)
        self.generate_button.grid(row=4, column=0, columnspan=2, pady=10)

        self.progress_label = tk.Label(self.root, text="")
        self.progress_label.grid(row=5, column=0, columnspan=2)

    def choose_main_image(self):
        self.main_image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
        if self.main_image_path:
            self.main_image_button.config(text=os.path.basename(self.main_image_path))

    def choose_small_images_folder(self):
        self.small_images_folder = filedialog.askdirectory()
        if self.small_images_folder:
            self.small_images_button.config(text=os.path.basename(self.small_images_folder))

    def generate_mosaic(self):
        if not self.main_image_path or not self.small_images_folder:
            messagebox.showerror("Error", "Please select both a main image and a folder of small images.")
            return

        try:
            self.target_width = int(self.width_entry.get())
            self.target_height = int(self.height_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Width and Height must be valid integers.")
            return

        self.progress_label.config(text="Generating mosaic, please wait...")
        self.root.update_idletasks()

        # Load images
        main_image = Image.open(self.main_image_path)
        main_image = main_image.resize((self.target_width, self.target_height))

        small_images = []
        for filename in os.listdir(self.small_images_folder):
            if filename.endswith('.jpg') or filename.endswith('.png'):
                img = Image.open(os.path.join(self.small_images_folder, filename))
                small_images.append(img)

        cols = 50  # 固定列數
        rows = math.ceil(self.target_height / (self.target_width / cols))

        thumb_width = self.target_width // cols
        thumb_height = self.target_height // rows

        small_images_resized = [img.resize((thumb_width, thumb_height)) for img in small_images]
        small_images_np = [np.array(img) for img in small_images_resized]

        while len(small_images_np) < rows * cols:
            small_images_np.append(random.choice(small_images_np))

        random.shuffle(small_images_np)

        mosaic_image = np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)

        def match_and_paste(i, j):
            box = (j * thumb_width, i * thumb_height, (j + 1) * thumb_width, (i + 1) * thumb_height)
            main_block = np.array(main_image.crop(box))
            main_avg_color = np.mean(main_block, axis=(0, 1))

            best_match = min(small_images_np,
                             key=lambda img: np.linalg.norm(np.mean(img, axis=(0, 1)) - main_avg_color))

            color_ratio = main_avg_color / np.mean(best_match, axis=(0, 1))
            best_match_adjusted = np.clip(best_match * color_ratio, 0, 255).astype(np.uint8)

            mosaic_image[i * thumb_height:(i + 1) * thumb_height, j * thumb_width:(j + 1) * thumb_width,
            :] = best_match_adjusted

        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(rows):
                for j in range(cols):
                    futures.append(executor.submit(match_and_paste, i, j))
            for future in futures:
                future.result()

        mosaic_image_pil = Image.fromarray(mosaic_image)
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if save_path:
            mosaic_image_pil.save(save_path)
            mosaic_image_pil.show()

        self.progress_label.config(text="Mosaic generation complete!")


if __name__ == "__main__":
    root = tk.Tk()
    app = MosaicGeneratorApp(root)
    root.mainloop()
