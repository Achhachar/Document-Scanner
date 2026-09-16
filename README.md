# Methodology & Algorithmic Pipeline

An overview of the computer vision pipeline employed to isolate paper boundaries, rectify perspective distortion, and produce clean, legible digital documents.

---

### 1. Spatial Downsampling & Scale Preservation
High-resolution camera captures contain fine grain and high-frequency textures that unnecessarily slow down image processing and create false edge detections. 

* **Working Resolution:** The input image is scaled down to a standardised height for geometric analysis.
* **Scale Ratio Tracking:** A scaling factor is retained to map the identified corner coordinates back to the original uncompressed image, ensuring the final scan retains full optical clarity without blur.

---

### 2. Greyscale Conversion & Noise Suppression
Before delineating document edges, internal distractions such as printed text, creases, and paper grain must be softened whilst preserving external boundaries.

* **Greyscale Conversion:** Colour channels are combined into a single-channel intensity image, isolating structural contrast from colour variance.
* **Gaussian Filtering:** A subtle blur smooths out small sensor artefacts and high-contrast lettering so that subsequent edge detection responds primarily to the document's outer boundary.

---

### 3. Edge Detection
The Canny edge detection algorithm isolates structural transitions across the scene through a three-stage mechanism:

* **Gradient Computation:** Detects sharp changes in pixel brightness horizontally and vertically.
* **Thinning:** Suppresses pixels that are not the local peak along the gradient direction, leaving razor-thin outlines.
* **Hysteresis Thresholding:** Retains strong edges whilst discarding faint noise. Intermediate edges are kept only if physically connected to a confirmed strong boundary.

---

### 4. Contour Extraction & Salience Filtering
The isolated edge segments are vectorised into continuous closed shapes:

* **Topological Tracing:** Border-following routines extract geometric contours from the binary edge map.
* **Area Prioritisation:** The extracted contours are ranked by enclosed surface area. The system focuses exclusively on the largest contours, under the reasonable assumption that the document is the dominant subject in frame.

---

### 5. Polygonal Approximation
Real-world paper edges are rarely geometrically pristine due to lens distortion, slight camera curvature, or imperfect paper alignment.

* **Shape Simplification:** The Ramer-Douglas-Peucker algorithm simplifies complex, jagged contours into clean polygonal approximations based on a perimeter-relative tolerance.
* **Quadrilateral Constraint:** The pipeline iterates through candidate shapes until it identifies a polygon that reduces to exactly four vertices, representing the four corners of a sheet.

---

### 6. Canonical Point Ordering
To apply an unwarping transform, the four detected vertices must be deterministically mapped to specific positions: Top-Left, Top-Right, Bottom-Right, and Bottom-Left.

* **Sum Heuristic:** The vertex with the smallest sum of coordinates corresponds to the top-left, whilst the largest sum indicates the bottom-right.
* **Difference Heuristic:** The vertex with the smallest difference between its coordinates identifies the top-right, whilst the largest difference indicates the bottom-left.

---

### 7. Perspective Transformation (Homography)
Once the corners are strictly indexed, perspective distortion caused by off-angle photography is corrected:

* **True Dimension Estimation:** The width and height of the destination rectangle are derived from the maximum Euclidean lengths of opposing edges, preventing anisotropic stretching.
* **Homography Matrix:** A transformation matrix maps the skewed four-point boundary into a flat, top-down rectangular canvas.
* **Bilinear Warping:** The transformation is applied directly to the full-resolution source image, interpolating pixels onto the planar canvas for an orthogonal, bird's-eye view.

---

### 8. Adaptive Thresholding
Mobile scans frequently suffer from non-uniform ambient light, lens vignetting, and hand-cast shadows, rendering global thresholding techniques ineffective.

* **Local Neighbourhood Evaluation:** The threshold for every pixel is calculated dynamically based on the weighted mean of its immediate surrounding window.
* **High-Contrast Binarisation:** Pixels darker than their immediate surroundings become clean text strokes, whilst the unevenly lit background is normalised to uniform white.