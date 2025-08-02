import os
import io
import numpy as np
from PIL import Image
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import cv2
import tensorflow as tf
from tensorflow.keras.models import load_model
import threading
import time

# Create blueprint
retino_blueprint = Blueprint('retino', __name__)

# Global model variable
model = None
model_lock = threading.Lock()
model_loaded = False

def load_model_optimized():
    """Load and optimize the model for faster inference"""
    global model, model_loaded
    
    try:
        MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'diabetic-retino-model.h5')
        print(f"Loading model from: {MODEL_PATH}")
        
        # Configure TensorFlow for optimal performance
        tf.config.threading.set_inter_op_parallelism_threads(0)  # Use all available cores
        tf.config.threading.set_intra_op_parallelism_threads(0)  # Use all available cores
        
        # Load model without compilation for faster loading
        model = load_model(MODEL_PATH, compile=False)
        
        # Compile with optimized settings
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy'],
            run_eagerly=False  # Use graph mode for better performance
        )
        
        # Warm up the model with a dummy prediction to initialize all layers
        print("Warming up model...")
        dummy_input = np.random.random((1, 224, 224, 3)).astype(np.float32)
        _ = model.predict(dummy_input, verbose=0)
        
        model_loaded = True
        print("Model loaded and warmed up successfully!")
        
    except Exception as e:
        print(f"Error loading model: {e}")
        model_loaded = False

def ensure_model_loaded():
    """Ensure model is loaded before making predictions"""
    global model, model_loaded
    
    if not model_loaded:
        with model_lock:
            if not model_loaded:  # Double-check locking pattern
                load_model_optimized()
    
    return model_loaded

# Load model on import (but in a separate thread to not block startup)
def background_model_load():
    load_model_optimized()

# Start loading model in background
model_thread = threading.Thread(target=background_model_load, daemon=True)
model_thread.start()

def is_regular_photo(image):
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    height, width = gray.shape
    border_size = min(width, height) // 10
    borders = np.concatenate([
        gray[:border_size, :].flatten(),
        gray[-border_size:, :].flatten(),
        gray[:, :border_size].flatten(),
        gray[:, -border_size:].flatten()
    ])
    if np.mean(borders) < 50:
        return False, ""
    if lines is not None and len(lines) > 5:
        return True, "This appears to be a photograph with straight lines."
    return False, ""

def is_medical_image(image):
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
    is_grayscale = len(img_array.shape) == 2 or (len(img_array.shape) == 3 and np.allclose(img_array[:,:,0], img_array[:,:,1], atol=5))
    if not is_grayscale:
        return False, ""
    mean_brightness = np.mean(gray)
    std_dev = np.std(gray)
    if mean_brightness > 100 and std_dev < 60:
        return True, "This appears to be an X-ray or medical scan image."
    return False, ""

def is_fundus_image(image):
    is_photo, msg = is_regular_photo(image)
    if is_photo:
        return False, msg
    is_med, msg = is_medical_image(image)
    if is_med:
        return False, msg
    img_array = np.array(image)
    if len(img_array.shape) != 3 or img_array.shape[2] != 3:
        return False, "Image must be in color."
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    height, width = gray.shape
    border_size = min(width, height) // 10
    borders = np.concatenate([
        gray[:border_size, :].flatten(),
        gray[-border_size:, :].flatten(),
        gray[:, :border_size].flatten(),
        gray[:, -border_size:].flatten()
    ])
    has_dark_borders = np.mean(borders) < 50
    min_dim = min(height, width)
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1, minDist=min_dim//2,
        param1=40, param2=20, minRadius=min_dim//5, maxRadius=int(min_dim * 0.8)
    )
    color_mask = ((hsv[:,:,0] >= 0) & (hsv[:,:,0] <= 50)) | ((hsv[:,:,0] >= 150) & (hsv[:,:,0] <= 180))
    color_percentage = np.mean(color_mask)
    if has_dark_borders and (circles is not None or color_percentage > 0.1):
        return True, "Valid fundus image"
    return False, "The image does not appear to be a retinal fundus photograph."

def predict_image(image):
    try:
        # Ensure model is loaded
        if not ensure_model_loaded():
            return None, "Model not loaded. Please try again."
        
        is_valid, message = is_fundus_image(image)
        if not is_valid:
            return None, message
            
        # Optimized image preprocessing
        img = image.resize((224, 224), Image.LANCZOS)  # Use LANCZOS for better quality
        img_array = np.array(img, dtype=np.float32) / 255.0  # Use float32 for better performance
        image_tensor = np.expand_dims(img_array, axis=0)
        
        # Make prediction with optimized settings
        with tf.device('/CPU:0'):  # Ensure CPU usage for consistency
            prediction = model.predict(image_tensor, verbose=0, batch_size=1)
        
        return float(prediction[0][0]), "Prediction successful"
    except Exception as e:
        return None, str(e)

# Add model warmup endpoint for faster first prediction
@retino_blueprint.route('/warmup', methods=['GET', 'POST'])
def warmup_model():
    """Endpoint to warm up the model for faster predictions"""
    try:
        if ensure_model_loaded():
            # Perform a dummy prediction to warm up the model
            dummy_input = np.random.random((1, 224, 224, 3)).astype(np.float32)
            _ = model.predict(dummy_input, verbose=0)
            return jsonify({'status': 'Model warmed up successfully'}), 200
        else:
            return jsonify({'error': 'Model not loaded'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add model status endpoint
@retino_blueprint.route('/model-status', methods=['GET'])
def model_status():
    """Check if model is loaded and ready"""
    return jsonify({
        'model_loaded': model_loaded,
        'status': 'ready' if model_loaded else 'loading'
    }), 200

@retino_blueprint.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    # Check if model is ready before processing
    if not model_loaded:
        return jsonify({'error': 'Model is still loading. Please try again in a few seconds.'}), 503
        
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Optimized image loading
        start_time = time.time()
        
        # Load image with optimized settings
        image = Image.open(file.stream)
        if image.mode != 'RGB':
            image = image.convert("RGB")
        
        # Fast prediction
        result, message = predict_image(image)
        
        processing_time = time.time() - start_time
        print(f"Prediction completed in {processing_time:.2f} seconds")
        
        if result is None:
            return jsonify({'error': message}), 400
            
        confidence = result * 100
        is_dr_detected = confidence < 50
        actual_confidence = 100 - confidence if is_dr_detected else confidence
        
        response = {
            'stage': 'DR Detected' if is_dr_detected else 'No DR Detected',
            'confidence': round(actual_confidence, 2),
            'processing_time': round(processing_time, 2),
            'recommendations': [
                'Schedule immediate consultation' if is_dr_detected else 'Schedule routine check-up in 12 months',
                'Monitor blood sugar levels regularly',
                'Maintain a healthy diet and lifestyle'
            ]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500
