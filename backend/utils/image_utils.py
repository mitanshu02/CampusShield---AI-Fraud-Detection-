# backend/utils/image_utils.py

import cv2
import numpy as np
from PIL import Image
import os
import uuid

GENERATED_DIR = os.path.join(os.path.dirname(__file__), "..", "generated")

def ensure_generated_dir():
    os.makedirs(GENERATED_DIR, exist_ok=True)

def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Could not load image: {path}")
    return img

def resize_to_standard(img: np.ndarray) -> np.ndarray:
    return cv2.resize(img, (1280, 720), interpolation=cv2.INTER_AREA)

def generate_heatmap(img1: np.ndarray, img2: np.ndarray) -> tuple:
    img1_resized = resize_to_standard(img1)
    img2_resized = resize_to_standard(img2)

    gray1 = cv2.cvtColor(img1_resized, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2_resized, cv2.COLOR_BGR2GRAY)

    diff = cv2.absdiff(gray1, gray2)

    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    kernel  = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(
        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    heatmap = img1_resized.copy()
    overlay = heatmap.copy()

    for contour in contours:
        if cv2.contourArea(contour) > 200:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(overlay, (x, y), (x + w, y + h),
                          (0, 0, 255), -1)

    cv2.addWeighted(overlay, 0.4, heatmap, 0.6, 0, heatmap)

    for contour in contours:
        if cv2.contourArea(contour) > 200:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(heatmap, (x, y), (x + w, y + h),
                          (0, 0, 255), 2)

    diff_count = np.count_nonzero(dilated)
    total_px   = dilated.shape[0] * dilated.shape[1]
    diff_pct   = (diff_count / total_px) * 100

    return heatmap, diff_pct

def save_image(img: np.ndarray, filename: str = None) -> str:
    ensure_generated_dir()
    if filename is None:
        filename = f"heatmap_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(GENERATED_DIR, filename)
    cv2.imwrite(filepath, img)
    return f"/generated/{filename}"

def save_screenshot(img: np.ndarray, filename: str) -> str:
    ensure_generated_dir()
    filepath = os.path.join(GENERATED_DIR, filename)
    cv2.imwrite(filepath, img)
    return f"/generated/{filename}"

def pil_to_cv2(pil_img) -> np.ndarray:
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def bytes_to_cv2(img_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)