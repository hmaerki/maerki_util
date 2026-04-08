"""
Fast Scanner Script with Device Caching
Optimized version that avoids slow sane.get_devices() calls by using cached device names.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import sane

# Cache file for storing the last known working device
DEVICE_CACHE_FILE = Path.home() / ".cache" / "pyscan_device_cache.json"


def load_device_cache():
    """Load cached device information."""
    try:
        if DEVICE_CACHE_FILE.exists():
            with open(DEVICE_CACHE_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_device_cache(device_name, device_info):
    """Save device information to cache."""
    try:
        DEVICE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {
            "device_name": device_name,
            "device_info": device_info,
            "last_used": datetime.now().isoformat(),
        }
        with open(DEVICE_CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save device cache: {e}")


def try_device_direct(device_name):
    """Try to open a device directly by name."""
    try:
        scanner = sane.open(device_name)
        scanner.close()
        return True
    except Exception:
        return False


def find_scanner_fast():
    """Find scanner using multiple speed optimization strategies."""
    print("Looking for Canon LiDE 220 scanner...")

    # Strategy 1: Try cached device first
    cache = load_device_cache()
    if cache.get("device_name"):
        cached_device = cache["device_name"]
        print(f"Trying cached device: {cached_device}")
        if try_device_direct(cached_device):
            print(f"✓ Found scanner using cache: {cached_device}")
            return cached_device, "Found in cache"

    # Strategy 2: Try common device name patterns for Canon LiDE scanners
    print("Trying common device patterns...")
    common_patterns = [
        "genesys:libusb:003:005",  # Your specific device
        "genesys:libusb:001:005",  # USB bus variations
        "genesys:libusb:002:005",
        "genesys:libusb:003:004",
        "genesys:libusb:003:006",
        "genesys:libusb:001:004",
        "genesys:libusb:002:004",
        "canon:libusb:003:005",  # Alternative driver names
        "canon:libusb:001:005",
        "canon_lide_220:libusb:003:005",
    ]

    for device_pattern in common_patterns:
        print(f"  Trying: {device_pattern}")
        if try_device_direct(device_pattern):
            print(f"✓ Found scanner: {device_pattern}")
            save_device_cache(device_pattern, "Canon LiDE 220")
            return device_pattern, "Found by pattern matching"

    # Strategy 3: Use environment variable if set
    env_device = os.environ.get("PYSCAN_DEVICE")
    if env_device:
        print(f"Trying environment device: {env_device}")
        if try_device_direct(env_device):
            print(f"✓ Found scanner from environment: {env_device}")
            save_device_cache(env_device, "Canon LiDE 220 (from env)")
            return env_device, "Found from environment variable"

    # Strategy 4: Last resort - full device enumeration
    print("Fast methods failed, performing full device scan...")
    try:
        devices = sane.get_devices()

        for device in devices:
            print(f"   Available: {device[1]} ({device[0]})")

        for device in devices:
            if (
                "canon" in device[1].lower()
                or "lide" in device[1].lower()
                or "genesys" in device[0].lower()
            ):
                device_name = device[0]
                device_info = device[1]
                print(f"✓ Found scanner: {device_info} ({device_name})")
                save_device_cache(device_name, device_info)
                return device_name, device_info

    except Exception as e:
        print(f"Error during device enumeration: {e}")

    return None, None


def auto_scan():
    """Automatically scan one page at 300 DPI."""
    print("Canon LiDE 220 Auto Scanner (Fast Version)")
    print("==========================================")

    try:
        # Initialize SANE
        print("Initializing scanner system...")
        sane.init()

        # Find Canon scanner using fast method
        canon_device, device_info = find_scanner_fast()

        if not canon_device:
            print("Canon LiDE 220 scanner not found!")
            print("\nTroubleshooting tips:")
            print("1. Make sure scanner is connected and powered on")
            print("2. Check if you have permission to access USB devices")
            print("3. Try running: sudo sane-find-scanner")
            print("4. Set PYSCAN_DEVICE environment variable to your device name")
            return False

        # Connect to scanner
        print(f"Connecting to scanner: {canon_device}")
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
        pil_image.save(output_path, optimize=True)

        # Print scan results
        print("✓ Scan completed successfully!")
        print(f"  Output file: {output_path}")
        print(f"  Image size: {pil_image.size[0]} x {pil_image.size[1]} pixels")
        print("  Resolution: 300 DPI")
        print(f"  Color mode: {pil_image.mode}")
        print(f"  File size: {Path(output_path).stat().st_size / 1024 / 1024:.1f} MB")
        print(f"  Device used: {canon_device}")

        # Close scanner
        scanner.close()
        sane.exit()

        return output_path

    except Exception as e:
        print(f"Error during scanning: {e}")
        try:
            sane.exit()
        except Exception:
            pass
        return False


def clear_cache():
    """Clear the device cache."""
    try:
        if DEVICE_CACHE_FILE.exists():
            DEVICE_CACHE_FILE.unlink()
            print("Device cache cleared.")
        else:
            print("No device cache found.")
    except Exception as e:
        print(f"Error clearing cache: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clear-cache":
        clear_cache()
        sys.exit(0)

    result = auto_scan()
    if result:
        print(f"\nScan saved as: {result}")
        sys.exit(0)
    else:
        print("\nScan failed!")
        sys.exit(1)
