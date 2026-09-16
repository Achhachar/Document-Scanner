# Methodology & Algorithmic Pipeline

An overview of the computer vision pipeline employed to isolate paper boundaries, rectify perspective distortion, and produce clean, legible digital documents with real-time binarisation tuning.

---

### 1. Spatial Downsampling & Scale Preservation
High-resolution camera captures contain fine grain and high-frequency textures that degrade computational throughput and introduce spurious edge responses.

* **Working Resolution:** The source image is scaled down to a standardised height of 500 px for geometric segmentation and contour analysis.
* **Scale Ratio Tracking:** An exact scale factor $r = \frac{\text{original\_height}}{\text{working\_height}}$ is retained to project all derived spatial coordinates back onto the full-resolution uncompressed matrix, ensuring zero optical degradation during transformation.

---

### 2. Greyscale Conversion & Noise Suppression
Internal print elements, creases, and surface textures must be attenuated whilst retaining distinct perimeter boundaries.

* **Greyscale Conversion:** Multi-channel RGB arrays are converted to single-channel luminance intensity.
* **Gaussian Filtering:** A spatial low-pass filter ($5 \times 5$ Gaussian kernel, $\sigma = 0$) smooths sensor noise and internal typography, preventing internal details from interfering with boundary isolation.

---

### 3. Edge Detection
The Canny edge detection algorithm identifies salient structural transitions across the scene:

* **Gradient Computation:** Calculates directional derivatives across horizontal and vertical axes to locate local intensity extrema.
* **Non-Maximum Suppression:** Thins wide gradient ridges to single-pixel-wide edge trajectories.
* **Hysteresis Thresholding:** Dual thresholds (75 and 200) retain definitive edge paths while systematically discarding floating noise artifacts.

---

### 4. Contour Extraction & Salience Filtering
The binary edge map is topologically parsed into closed-loop vector representations:

* **Topological Tracing:** Border-following routines retrieve external contours using simple chain approximation.
* **Area Prioritisation:** Extracted contours are sorted in descending order by enclosed surface area, operating on the heuristic that the document constitutes the dominant geometric subject within the scene.

---

### 5. Polygonal Approximation
Lens distortion and physical paper warping introduce minor curvature along edges that should ideally be linear.

* **Ramer-Douglas-Peucker Simplification:** Approximates complex, continuous contours into clean geometric polygons based on an arc-length tolerance ($\epsilon = 0.02 \times \text{Perimeter}$).
* **Quadrilateral Constraint:** The pipeline iterates through candidate contours until it isolates a polygon reducing strictly to four vertices ($N = 4$).

---

### 6. Canonical Point Ordering
Perspective rectification requires a deterministic mapping of the four vertices to fixed cartesian assignments: `[Top-Left, Top-Right, Bottom-Right, Bottom-Left]`.

* **Coordinate Sum ($x + y$):** The vertex with the minimal sum corresponds to the origin-adjacent **Top-Left**; the maximum sum denotes the **Bottom-Right**.
* **Coordinate Difference ($x - y$):** The minimum difference identifies the **Top-Right**; the maximum difference designates the **Bottom-Left**.

---

### 7. Perspective Transformation (Homography)
Planar projective distortion introduced by non-orthogonal capture angles is corrected through homography:

* **True Dimension Estimation:** Destination width and height are calculated via the maximum Euclidean norms between opposing vertices, preventing aspect ratio distortion.
* **Transformation Matrix:** OpenCV computes the $3 \times 3$ perspective transformation matrix $M$ between source coordinates and planar target coordinates.
* **High-Fidelity Warping:** The perspective transform is executed against the **original, full-resolution** image using bilinear interpolation, caching a high-detail greyscale scan in memory.

---

### 8. Interactive Adaptive Binarisation & Calibration
Non-uniform ambient lighting, specular reflections, and shadows render global binarisation (such as Otsu's thresholding) ineffective. To provide fine-grained control over varying paper textures and ink contrast, the system exposes an interactive real-time tuning interface.

* **Local Gaussian Neighbourhood:** Binarisation thresholds are computed per-pixel using a Gaussian-weighted local window to accommodate uneven lighting gradients.
* **Decoupled Viewport Scaling:** While adjustments are calculated across the full-resolution buffer, viewports are scaled dynamically to fit display bounds without compromising export fidelity.
* **Real-Time Sliders:**
  * **Block Size:** Modulates the local evaluation window. The GUI maps continuous integer slider values to strict odd values $\ge 3$ via $B = 2 \times \text{slider\_value} + 3$, balancing local detail retention against low-frequency shadow rejection.
  * **Constant Offset ($C$):** Governs foreground/background contrast sensitivity by tuning the local subtraction factor ($T(x,y) = \mu_{\text{local}} - C$).
* **State Persistence:** Keyboard hooks capture user input directly from the event loop:
  * Press `s` or `S` to write the full-resolution binarised scan to disk.
  * Press `Esc` or `q` to abort execution without overwriting data.