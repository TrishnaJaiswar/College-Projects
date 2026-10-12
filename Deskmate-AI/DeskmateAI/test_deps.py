import pystray
from PIL import Image

image = Image.new('RGB', (64, 64), color='blue')

def on_quit(icon, item):
    icon.stop()

icon = pystray.Icon("test", image, "Test Tray")
icon.run()