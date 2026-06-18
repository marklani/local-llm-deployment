from PIL import Image, ImageTk
import tkinter as tk
import os

class ImagePixelViewer:
    def __init__(self, master, image_path):
        self.master = master
        master.title("Image Pixel Viewer")
        self.image_path = image_path
        self.img = None
        self.tk_img = None

        # Load the image
        try:
            self.img = Image.open(self.image_path).convert("RGB")
        except FileNotFoundError:
            print(f"Error: Image file not found at {self.image_path}")
            master.destroy()
            return
        except Exception as e:
            print(f"Error loading image: {e}")
            master.destroy()
            return

        self.width = self.img.width
        self.height = self.img.height

        # Setup GUI elements
        self.canvas = tk.Canvas(master, width=self.width, height=self.height, bg='white')
        self.canvas.pack()

        self.info_label = tk.Label(master, text="Move mouse over the image to see pixel values.")
        self.info_label.pack(pady=10)

        # Display the image on the canvas
        self.tk_img = ImageTk.PhotoImage(self.img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        # Bind mouse motion event
        self.canvas.bind('<Motion>', self.on_mouse_move)

    def on_mouse_move(self, event):
        # Get pixel coordinates from the event
        x = int(event.x)
        y = int(event.y)

        # Check bounds just in case
        if 0 <= x < self.width and 0 <= y < self.height:
            # Get pixel data
            r, g, b = self.img.getpixel((x, y))

            # Update the info label
            pixel_info = f"Pixel at ({x}, {y}): RGB = ({r}, {g}, {b})"
            self.info_label.config(text=pixel_info)
        else:
            self.info_label.config(text="Cursor is outside the image bounds.")


if __name__ == '__main__':
    # IMPORTANT: Ensure you have an image named 'test_image.png'
    # in the same directory, and that you have Pillow and tkinter installed.
    image_file = "test_image.png"

    root = tk.Tk()
    app = ImagePixelViewer(root, image_file)
    root.mainloop()