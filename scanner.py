import cv2
import numpy as np

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_w = max(int(width_a), int(width_b))
    
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_h = max(int(height_a), int(height_b))
    
    dst = np.array([
        [0, 0],
        [max_w - 1, 0],
        [max_w - 1, max_h - 1],
        [0, max_h - 1]
    ], dtype="float32")
    
    m = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, m, (max_w, max_h))

def extract_document_quadrilateral(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")
        
    orig = image.copy()
    target_height = 500.0
    ratio = image.shape[0] / target_height
    target_width = int(image.shape[1] * (target_height / image.shape[0]))
    resized = cv2.resize(image, (target_width, int(target_height)))
    
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    screen_cnt = None

    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            screen_cnt = approx
            break

    if screen_cnt is None:
        raise ValueError("No quadrilateral document contour detected.")

    warped = four_point_transform(orig, screen_cnt.reshape(4, 2) * ratio)
    return cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

def run_interactive_tuner(warped_gray, output_path="scanned_output.png"):
    window_name = "Document Scanner Tuner"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    h, w = warped_gray.shape
    max_preview_h = 800
    display_scale = min(1.0, max_preview_h / float(h))
    
    state = {
        "processed_full": None
    }

    def update_view(*args):
        raw_block = cv2.getTrackbarPos("Block Size (odd)", window_name)
        c_val = cv2.getTrackbarPos("Constant (C)", window_name)
        
        block_size = (raw_block * 2) + 3
        
        binarised = cv2.adaptiveThreshold(
            warped_gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size, c_val
        )
        state["processed_full"] = binarised
        
        if display_scale < 1.0:
            preview = cv2.resize(binarised, (int(w * display_scale), int(h * display_scale)))
        else:
            preview = binarised
            
        cv2.imshow(window_name, preview)

    cv2.createTrackbar("Block Size (odd)", window_name, 4, 30, update_view)
    cv2.createTrackbar("Constant (C)", window_name, 10, 40, update_view)

    update_view()
    
    print("Press 's' to save and exit. Press 'q' or 'ESC' to abort.")
    
    while True:
        key = cv2.waitKey(50) & 0xFF
        if key in [ord('s'), ord('S')]:
            if state["processed_full"] is not None:
                cv2.imwrite(output_path, state["processed_full"])
                print(f"High-resolution scan written to: {output_path}")
            break
        elif key in [27, ord('q'), ord('Q')]:
            print("Operation cancelled without saving.")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    warped_buffer = extract_document_quadrilateral("document.jpg")
    run_interactive_tuner(warped_buffer, "final_scan.png")