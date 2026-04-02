"""
Hans: Simple, fast.
Hans: Detection of the scanner takes too long...

Simple Auto Scanner Script
Automatically scans one page at 300 DPI from Canon LiDE 220 without user interaction.
"""

import pathlib
import sys
from datetime import datetime

import sane

from .discover import FILENAME_USB_DEVICE, discover_canon_lide


def auto_scan():
    filename_usb_device = pathlib.Path(FILENAME_USB_DEVICE)
    if not filename_usb_device.exists():
        print(f"{FILENAME_USB_DEVICE}: File does not exist yet. Running: pyscan_linux_discover")
        device = discover_canon_lide()
    try:
        device = filename_usb_device.read_text()
    except FileNotFoundError as e:
        print(f"ERROR: {e!r}")
        return

    print(f"{FILENAME_USB_DEVICE}: found '{device}'!")

    try:
        sane.init()

        scanner = sane.open(device)

        scanner.mode = "Color"
        scanner.resolution = 300

        # Set scan area to full A4 page
        scanner.tl_x = 0  # Top-left X
        scanner.tl_y = 0  # Top-left Y
        scanner.br_x = 215.9  # Bottom-right X (A4 width in mm)
        scanner.br_y = 297.0  # Bottom-right Y (A4 height in mm)

        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"scan_300dpi_{timestamp}.png"

        scanner.start()
        image_data = scanner.snap()
        image_data.save(output_path, optimize=True)

        scanner.close()
        sane.exit()

        return output_path

    except Exception as e:
        try:
            sane.exit()
        except:
            pass
        raise


if __name__ == "__main__":
    result = auto_scan()
    if result:
        print(f"\nScan saved as: {result}")
        sys.exit(0)
    else:
        print("\nScan failed!")
        sys.exit(1)
