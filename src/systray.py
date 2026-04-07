from pystray import Icon
from PIL import Image, ImageDraw
import threading

class RGBTrayIcon:
    def __init__(self, name='RGBIcon'):
        self.name = name
        self.icon = Icon(self.name)
        self.images = {}       # Stores precomputed PIL images
        self.current_mode = None

    def add_mode(self, key, rgb):
        """
        Add a mode with key and RGB value, precomputing its icon image.
        """
        if rgb == None:
            return
        if len(rgb) != 3 or not all(0 <= x <= 255 for x in rgb):
            raise ValueError("RGB must be a list of 3 integers between 0 and 255")
        self.images[key] = self._create_icon_image(rgb)

    def _create_icon_image(self, rgb, size=256):
        """
        Create a circular icon image.
        """
        # Ensure rgb is a tuple of ints
        rgb_tuple = tuple(int(x) for x in rgb)
        
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((0, 0, size, size), fill=rgb_tuple)
        return image

    def set_mode(self, key):
        """
        Set the icon using a precomputed image.
        """
        if key not in self.images:
            return
        self.current_mode = key
        self.icon.icon = self.images[key]

    def show(self):
        """
        Show the tray icon.
        """
        threading.Thread(target=self.icon.run, daemon=True).start()
