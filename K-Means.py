import cv2
import numpy as np
from sklearn.cluster import KMeans
from skimage.metrics import structural_similarity as ssim

# Load the image
image = cv2.imread("/content/drive/MyDrive/SEE Project/CUHK Face Sketch Database/photos/f-005-01.jpg")

# Convert the image to the RGB color space
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Preprocess the image (e.g., apply non-local means denoising)
image_denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

# Reshape the image into a 2D array of pixels
pixels = image_denoised.reshape(-1, 3)

# Apply K-means clustering with a higher number of clusters
kmeans = KMeans(n_clusters=32, random_state=42)
kmeans.fit(pixels)

# Replace each pixel with the centroid value of its cluster
sketch = kmeans.cluster_centers_[kmeans.labels_]

# Reshape the sketch back into an image
sketch = sketch.reshape(image.shape)

# Convert the sketch from float to uint8 and clip values to the valid range
sketch = np.clip(sketch.astype('uint8'), 0, 255)

# Convert the sketch to grayscale
sketch_gray = cv2.cvtColor(sketch, cv2.COLOR_RGB2GRAY)

# Save the black and white sketch image
cv2.imwrite("/content/drive/MyDrive/SEE Project/CHUK2_bw.png", sketch_gray)

# Calculate Mean Squared Error (MSE)
mse = np.mean((image_denoised.astype(float) - sketch.astype(float)) ** 2)

# Calculate Peak Signal-to-Noise Ratio (PSNR)
max_pixel = 255.0
psnr = 10 * np.log10((max_pixel ** 2) / mse)

# Calculate Structural Similarity Index (SSIM)
ssim_index, _ = ssim(cv2.cvtColor(image_denoised, cv2.COLOR_RGB2GRAY), sketch_gray, full=True)

print("Mean Squared Error (MSE):", mse)
print("Peak Signal-to-Noise Ratio (PSNR):", psnr)
print("Structural Similarity Index (SSIM):", ssim_index)
