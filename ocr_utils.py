import cv2
import pytesseract
import re
import numpy as np
from PIL import Image

# If Windows → set Tesseract path
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Regex for certificate IDs
CERT_ID_REGEX = re.compile(r'[A-Z]{2,3}\d{4}[A-Z]{2,4}\d{1,4}|FAKE\d{1,6}', re.IGNORECASE)

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not open {image_path}")

    # 1. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Denoise to remove small dots/noise
    gray = cv2.fastNlMeansDenoising(gray, h=30)

    # 3. Histogram Equalization (improves text visibility)
    gray = cv2.equalizeHist(gray)

    # 4. Adaptive Threshold for better binarization
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )

    # 5. Morphological Opening (remove small specks)
    kernel = np.ones((1, 1), np.uint8)
    clean = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)

    return clean

def extract_text(image_path):
    img = preprocess_image(image_path)

    # Try multiple Tesseract configurations
    configs = [
        "--psm 6 --oem 3",  # Assume block of text, LSTM OCR engine
        "--psm 7 --oem 3",  # Single line
        "--psm 11 --oem 3", # Sparse text
    ]

    best_text = ""
    for cfg in configs:
        text = pytesseract.image_to_string(img, config=cfg)
        text = text.replace("\n", " ").strip()
        if len(text) > len(best_text):
            best_text = text

    return best_text

def correct_ocr_errors(text):
    corrections = {
        "O": "0", "o": "0",
        "I": "1", "l": "1",
        "S": "5", "B": "8"
    }
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)
    return text

def normalize_cert_id(cert_id):
    return re.sub(r'[^A-Z0-9]', '', cert_id.upper())

def find_cert_id(text):
    if not text:
        return None
    clean_text = correct_ocr_errors(text.upper())
    matches = CERT_ID_REGEX.findall(clean_text)
    if matches:
        return matches[0].strip().upper()
    fallback = re.findall(r'[A-Z0-9]{6,20}', clean_text)
    if fallback:
        return fallback[0].upper()
    return None

def verify_certificate(image_path, manual_id=None, database=None):
    text = extract_text(image_path)
    cert_id = find_cert_id(text)

    if not cert_id and manual_id:
        cert_id = manual_id.strip().upper()

    if not cert_id:
        return "⚠️ Certificate ID not detected. Enter manually."

    cert_norm = normalize_cert_id(cert_id)
    if database:
        for db_id in database:
            if normalize_cert_id(db_id) == cert_norm:
                return f"✅ Certificate valid: {cert_norm}"
        return f"❌ Certificate not valid: {cert_norm}"
    return f"🔎 Extracted Cert ID: {cert_norm}"
