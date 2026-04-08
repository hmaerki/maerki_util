"""
Hans: Simple, fast.
Hans: Detection of the scanner takes too long...

Simple Auto Scanner Script
Automatically scans one page at 300 DPI from Canon LiDE 220 without user interaction.
"""

import sys
from datetime import datetime
from pathlib import Path

import sane


def auto_scan():
    """Automatically scan one page at 300 DPI."""
    print("Canon LiDE 220 Auto Scanner")
    print("===========================")

    try:
        # Initialize SANE
        print("Initializing scanner system...")
        sane.init()

        # Find Canon scanner
        print("Looking for Canon LiDE 220 scanner...")
        devices = sane.get_devices()

        for device in devices:
            print(f"   scanner: {device[1]} ({device[0]})")

        canon_device = None
        for device in devices:
            if (
                "canon" in device[1].lower()
                or "lide" in device[1].lower()
                or "genesys" in device[0].lower()
            ):
                canon_device = device[0]
                print(f"Found scanner: {device[1]} ({device[0]})")
                break

        if not canon_device:
            print("Canon LiDE 220 scanner not found!")
            print("Available devices:")
            for device in devices:
                print(f"  - {device[1]} ({device[0]})")
            return False

        # Connect to scanner
        print(f"Connecting to scanner... {canon_device}")
        scanner = sane.open(canon_device)

        # Configure scanner settings
        print("Configuring scanner for 300 DPI color scan...")

        # Set scan mode to color
        if hasattr(scanner, "mode"):
            scanner.mode = "Color"

        # Set resolution to 300 DPI
        if hasattr(scanner, "resolution"):
            scanner.resolution = 300

        # Set scan area to full A4 page
        if hasattr(scanner, "tl_x"):
            scanner.tl_x = 0  # Top-left X
        if hasattr(scanner, "tl_y"):
            scanner.tl_y = 0  # Top-left Y
        if hasattr(scanner, "br_x"):
            scanner.br_x = 215.9  # Bottom-right X (A4 width in mm)
        if hasattr(scanner, "br_y"):
            scanner.br_y = 297.0  # Bottom-right Y (A4 height in mm)

        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"scan_300dpi_{timestamp}.png"

        # Scan the document
        print("Scanning document at 300 DPI...")
        print("Please make sure your document is placed on the scanner bed.")

        # Start scanning
        scanner.start()

        # Get the scanned image
        image_data = scanner.snap()

        # Convert to PIL Image and save
        pil_image = image_data
        # pil_image = Image.fromarray(image_data)
        pil_image.save(output_path, optimize=True)

        # Print scan results
        print("✓ Scan completed successfully!")
        print(f"  Output file: {output_path}")
        print(f"  Image size: {pil_image.size[0]} x {pil_image.size[1]} pixels")
        print("  Resolution: 300 DPI")
        print(f"  Color mode: {pil_image.mode}")
        print(f"  File size: {Path(output_path).stat().st_size / 1024 / 1024:.1f} MB")

        # Close scanner
        scanner.close()
        sane.exit()

        return output_path

    except Exception as e:
        print(f"Error during scanning: {e}")
        try:
            sane.exit()
        except:
            pass
        raise
        return False


if __name__ == "__main__":
    result = auto_scan()
    if result:
        print(f"\nScan saved as: {result}")
        sys.exit(0)
    else:
        print("\nScan failed!")
        sys.exit(1)
