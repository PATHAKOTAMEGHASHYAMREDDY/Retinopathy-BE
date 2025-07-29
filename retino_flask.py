import os
import io
import numpy as np
from PIL import Image
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import cv2
import tensorflow as tf
from tensorflow.keras.models import load_model

# Create blueprint
retino_blueprint = Blueprint('retino', __name__)

# Load model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'diabetic-retino-model.h5')
print(f"Loading model from: {MODEL_PATH}")  # Debug print
model = load_model(MODEL_PATH, compile=False)
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

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
        is_valid, message = is_fundus_image(image)
        if not is_valid:
            return None, message
            
        # Preprocess image
        img = image.resize((224, 224))
        img_array = np.array(img) / 255.0
        image_tensor = np.expand_dims(img_array, axis=0)
        
        # Make prediction
        prediction = model.predict(image_tensor, verbose=0)
        return float(prediction[0][0]), "Prediction successful"
    except Exception as e:
        return None, str(e)

@retino_blueprint.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
        
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        image = Image.open(file.stream).convert("RGB")
        result, message = predict_image(image)
        
        if result is None:
            return jsonify({'error': message}), 400
            
        confidence = result * 100
        is_dr_detected = confidence < 50
        actual_confidence = 100 - confidence if is_dr_detected else confidence
        
        response = {
            'stage': 'DR Detected' if is_dr_detected else 'No DR Detected',
            'confidence': round(actual_confidence, 2),
            'recommendations': [
                'Schedule immediate consultation' if is_dr_detected else 'Schedule routine check-up in 12 months',
                'Monitor blood sugar levels regularly',
                'Maintain a healthy diet and lifestyle'
            ]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
