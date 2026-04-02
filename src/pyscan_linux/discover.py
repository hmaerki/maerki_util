#!/usr/bin/env python3
"""
Scanner Device Discovery Tool
This tool helps you find the exact device name for your scanner.
Run this once to discover the device name, then use it in your scanning script.
"""

import pathlib

import sane

FILENAME_USB_DEVICE = "pyscan_linux_usb_device.txt"


def discover_canon_lide():
    print("Scanner Discovery")

    sane.init()

    devices = sane.get_devices()
    if not devices:
        print("No scanners found!")
        return

    print("scanners found:")

    for device in devices:
        device_name = device[0]
        device_description = device[1] if len(device) > 1 else "Unknown"
        device_manufacturer = device[2] if len(device) > 2 else "Unknown"
        device_type = device[3] if len(device) > 3 else "Unknown"

        print(f"  Name:           {device_name}")
        print(f"    Description:  {device_description}")
        print(f"    Manufacturer: {device_manufacturer}")
        print(f"    Type:         {device_type}")

    # Check if this looks like a Canon LiDE scanner
    for device in devices:
        if (
            "canon" in device[1].lower()
            or "lide" in device[1].lower()
            or "genesys" in device[0].lower()
        ):
            print(
                f"Write '{device[0]}' into '{FILENAME_USB_DEVICE}'!"
            )
            pathlib.Path(FILENAME_USB_DEVICE).write_text(device[0])
            break
    else:
        print("ERROR: no matching scanner found!")

    try:
        sane.exit()
    except Exception:
        pass


if __name__ == "__main__":
    discover_canon_lide()
