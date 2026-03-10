import qrcode

# Text to encode (URL, plain text, etc.)
data = "https://unsloth.ai/docs/models/qwen3.5"

# Generate QR code

qr = qrcode.QRCode(
    version=None,               # Auto-size based on data length
    error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium tolerance for errors
    box_size=10,                # Size of each block (pixel)
    border=4                    # Padding around the code
)

qr.add_data(data)
qr.make(fit=True)                 # Automatically adjust version to fit text

# Generate image file
img = qr.make_image(fill_color="black", back_color="white")
img.save("qr_code.png")

print(f"QR code generated successfully for: {data}")