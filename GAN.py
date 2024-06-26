import os
import re
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr


# Function to sort files alphanumerically
def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('(\[0-9\]+)', key)]
    return sorted(data, key=alphanum_key)

# Function to save generated images
def save_generated_images(images, epoch):
    os.makedirs('/content/drive/MyDrive/SEE Project/generated_images(1)', exist_ok=True)
    for i, img in enumerate(images):
        keras.preprocessing.image.save_img(f'/content/drive/MyDrive/SEE Project/generated_images(1)/generated_image_{epoch}_{i}.png', img)

# Define image size
SIZE = 256

# Load and preprocess images
image_path = '/content/drive/MyDrive/SEE Project/CUHK Face Sketch Database/photos'
img_array = []
image_files = sorted_alphanumeric(os.listdir(image_path))

for image in image_files:
    img = keras.preprocessing.image.load_img(os.path.join(image_path, image), target_size=(SIZE, SIZE))
    img = keras.preprocessing.image.img_to_array(img)
    img_array.append(img)

img_array = np.array(img_array) / 127.5 - 1  # Normalize images to [-1, 1]

# Load and preprocess sketches
sketch_path = '/content/drive/MyDrive/SEE Project/CUHK Face Sketch Database/sketches'
sketch_array = []
sketch_files = sorted_alphanumeric(os.listdir(sketch_path))

for sketch in sketch_files:
    img = keras.preprocessing.image.load_img(os.path.join(sketch_path, sketch), target_size=(SIZE, SIZE), color_mode='grayscale')
    img = keras.preprocessing.image.img_to_array(img)
    sketch_array.append(img)

sketch_array = np.array(sketch_array) / 127.5 - 1  # Normalize sketches to [-1, 1]

# Split data into train and test sets
train_images, test_images, train_sketches, test_sketches = train_test_split(img_array, sketch_array, test_size=0.2, random_state=42)

# Define the generator model
def build_generator():
    inputs = layers.Input(shape=(SIZE, SIZE, 3))

    # Encoder
    x = layers.Conv2D(64, kernel_size=4, strides=2, padding='same')(inputs)
    x = layers.LeakyReLU(alpha=0.2)(x)
    x = layers.Conv2D(128, kernel_size=4, strides=2, padding='same')(x)
    x = layers.LeakyReLU(alpha=0.2)(x)
    x = layers.Conv2D(256, kernel_size=4, strides=2, padding='same')(x)
    x = layers.LeakyReLU(alpha=0.2)(x)
    x = layers.Conv2D(512, kernel_size=4, strides=2, padding='same')(x)
    x = layers.LeakyReLU(alpha=0.2)(x)
    x = layers.Conv2D(512, kernel_size=4, strides=2, padding='same')(x)
    x = layers.LeakyReLU(alpha=0.2)(x)

    # Decoder
    x = layers.Conv2DTranspose(512, kernel_size=4, strides=2, padding='same')(x)
    x = layers.ReLU()(x)
    x = layers.Conv2DTranspose(256, kernel_size=4, strides=2, padding='same')(x)
    x = layers.ReLU()(x)
    x = layers.Conv2DTranspose(128, kernel_size=4, strides=2, padding='same')(x)
    x = layers.ReLU()(x)
    x = layers.Conv2DTranspose(64, kernel_size=4, strides=2, padding='same')(x)
    x = layers.ReLU()(x)
    x = layers.Conv2DTranspose(1, kernel_size=4, strides=2, padding='same', activation='tanh')(x)

    return keras.Model(inputs=inputs, outputs=x)

# Define the discriminator model
def build_discriminator():
    inputs = layers.Input(shape=(SIZE, SIZE, 1))

    x = layers.Conv2D(64, kernel_size=4, strides=2, padding='same')(inputs)
    x = layers.LeakyReLU(alpha=0.2)(x)
    x = layers.Conv2D(128, kernel_size=4, strides=2, padding='same')(x)
    x = layers.LeakyReLU(alpha=0.2)(x)
    x = layers.Conv2D(256, kernel_size=4, strides=2, padding='same')(x)
    x = layers.LeakyReLU(alpha=0.2)(x)
    x = layers.Conv2D(512, kernel_size=4, strides=2, padding='same')(x)
    x = layers.LeakyReLU(alpha=0.2)(x)
    x = layers.Flatten()(x)
    x = layers.Dense(1)(x)
    outputs = layers.Activation('sigmoid')(x)

    return keras.Model(inputs=inputs, outputs=outputs)

# Build and compile the models
generator = build_generator()
discriminator = build_discriminator()

discriminator.compile(optimizer=keras.optimizers.Adam(learning_rate=0.0002, beta_1=0.5),
                      loss='binary_crossentropy')

# Define the combined model
sketch_input = layers.Input(shape=(SIZE, SIZE, 3))
generated_sketch = generator(sketch_input)
discriminator.trainable = False
validity = discriminator(generated_sketch)
combined = keras.Model(sketch_input, [validity, generated_sketch])
combined.compile(optimizer=keras.optimizers.Adam(learning_rate=0.0002, beta_1=0.5),
                 loss=['binary_crossentropy', 'mae'],
                 loss_weights=[1, 100])

# Train the GAN
EPOCHS = 2000
BATCH_SIZE = 32

for epoch in range(EPOCHS):
    # Train the discriminator
    idx = np.random.randint(0, train_images.shape[0], BATCH_SIZE)
    real_sketches = train_sketches[idx]
    real_images = train_images[idx]
    generated_sketches = generator.predict(real_images)

    d_loss_real = discriminator.train_on_batch(real_sketches, np.ones((BATCH_SIZE, 1)))
    d_loss_fake = discriminator.train_on_batch(generated_sketches, np.zeros((BATCH_SIZE, 1)))
    d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)

    # Train the generator
    idx = np.random.randint(0, train_images.shape[0], BATCH_SIZE)
    real_images = train_images[idx]
    g_loss = combined.train_on_batch(real_images, [np.ones((BATCH_SIZE, 1)), train_sketches[idx]])

    # Print progress
    print(f"Epoch {epoch+1}/{EPOCHS} - Discriminator Loss: {d_loss:.4f}, Generator Loss: {g_loss[0]:.4f}")

    # Periodically save generated images
    if epoch == EPOCHS - 1:  # Save images at the last epoch
        generated_images = generator.predict(test_images)
        save_generated_images(generated_images, epoch)

# Evaluate the model
generated_sketches = generator.predict(test_images)

ssim_scores = []
psnr_scores = []
for i in range(len(test_sketches)):
    #ssim_score = ssim(test_sketches[i], generated_sketches[i], win_size=3, data_range=generated_sketches[i].max() - generated_sketches[i].min(), channel_axis=None)
    ssim_score = ssim(test_sketches[i], generated_sketches[i], data_range=generated_sketches[i].max() - generated_sketches[i].min(), multichannel=True)
    psnr_score = psnr(test_sketches[i], generated_sketches[i], data_range=generated_sketches[i].max() - generated_sketches[i].min())
    ssim_scores.append(ssim_score)
    psnr_scores.append(psnr_score)

print(f"Average SSIM: {np.mean(ssim_scores):.4f}")
print(f"Average PSNR: {np.mean(psnr_scores):.4f}")

# Save the trained generator model
generator.save('/content/drive/MyDrive/SEE Project/sketch_generator.h5')
