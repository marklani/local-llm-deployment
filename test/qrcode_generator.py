import qrcode
from PIL import Image # Pillow library

def generate_basic_qrcode(data_to_encode, filename="basic_qrcode.png", fill_color="black", back_color="white"):
    """Generates a standard QR code with solid colors."""

    # 1. Create the QR code object
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        #gap=5,
    )

    # 2. Add data and generate the structure
    qr.add_data(data_to_encode)
    qr.make(fit=True)

    # 3. Create the image (using Pillow directly)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    # 4. Save the image
    img.save(filename)
    print(f"✅ Success! Basic QR Code saved as: {filename}")

# Example usage:
generate_basic_qrcode("https://www.example.com", "basic_example.png", fill_color="blue")
