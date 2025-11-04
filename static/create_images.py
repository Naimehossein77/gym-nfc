#!/usr/bin/env python3
import base64

# Minimal PNG data for a 1x1 blue pixel (icon)
icon_png_data = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU8vNgAAAABJRU5ErkJggg=="
)

# Minimal PNG data for a 1x1 green pixel (logo)  
logo_png_data = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

with open("icon.png", "wb") as f:
    f.write(icon_png_data)

with open("logo.png", "wb") as f:
    f.write(logo_png_data)

print("Created placeholder icon.png and logo.png")