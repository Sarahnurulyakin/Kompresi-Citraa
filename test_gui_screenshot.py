import os
import sys
import time
from PIL import ImageGrab

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from gui.app import App

def main():
    print("Starting App in test mode...")
    app = App()
    
    # Wait for window to load
    app.update()
    
    # Set the file path directly to bypass the dialog
    test_image = os.path.abspath("bmp_dataset/img1.bmp")
    print(f"Loading test image: {test_image}")
    
    # Simulate selecting the image
    app.file_path = test_image
    app.display_preview(app.lbl_orig_preview, test_image)
    
    # Get image details and update labels
    from gui.app import get_image_details
    details = get_image_details(test_image)
    if details:
        app.lbl_orig_info.configure(text=f"{details['width']} x {details['height']} | {details['size']/1024:.2f} KB | {details['mode']}")
        detail_text = f"File: {os.path.basename(test_image)}\n"
        detail_text += f"Dimensi: {details['width']} x {details['height']}\n"
        detail_text += f"Format: BMP ({details['mode']})\n"
        detail_text += f"Ukuran: {details['size']/1024:.2f} KB\n"
        app.lbl_details_text.configure(text=detail_text, text_color=("#1e293b", "#f8fafc"))
    
    app.btn_compress.configure(state="normal")
    app.update()
    
    print("Running compression...")
    app.compress_image()
    app.update()
    
    print("Saving screenshot...")
    # Get window position and grab the screenshot
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()
    
    # Wait a bit for GUI to draw completely
    time.sleep(1)
    app.update()
    
    # Take screenshot of the app window
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save("screenshot_test.png")
    print("Screenshot saved to screenshot_test.png")
    
    app.destroy()

if __name__ == "__main__":
    main()
