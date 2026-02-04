# Diabetic Retinopathy Detection - Backend

Backend API service for the automated detection and classification of Diabetic Retinopathy (DR) using deep learning models.

## Overview

This repository provides the server-side infrastructure for processing retinal fundus images. It implements a Convolutional Neural Network (CNN) pipeline to categorize DR severity into five distinct clinical stages.

## Technology Stack

* **Language**: Python 3.8+
* **Framework**: Flask / FastAPI
* **Deep Learning**: TensorFlow / Keras
* **Computer Vision**: OpenCV, Pillow
* **Numerical Computing**: NumPy

## Features

* **Image Preprocessing**: Automated resizing, normalization, and Contrast Limited Adaptive Histogram Equalization (CLAHE).
* **Model Inference**: Staging images from "No DR" to "Proliferative DR".
* **RESTful API**: Endpoints for handling image uploads and returning diagnostic JSON data.
* **Ensemble Support**: Optimized for high-fidelity prediction using pre-trained weights.

## API Specification

### Predict Severity

* **Endpoint**: `/predict`
* **Method**: `POST`
* **Content-Type**: `multipart/form-data`
* **Payload**: `file` (Image: JPEG, PNG)
* **Success Response**:
```json
{
  "class": 2,
  "label": "Moderate",
  "confidence": 0.942,
  "status": "success"
}

```



## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/PATHAKOTAMEGHASHYAMREDDY/Retinopathy-BE.git
cd Retinopathy-BE

```


2. **Configure Environment**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

```


3. **Install Dependencies**:
```bash
pip install -r requirements.txt

```


4. **Model Deployment**:
Ensure the trained model weights (e.g., `model.h5` or `best_model.pth`) are placed in the `/models` directory.

## Execution

Run the development server:

```bash
python app.py

```

The API will be accessible at `http://localhost:5000`.

## Classification Logic

The system classifies images into the following categories:

* **0**: No DR
* **1**: Mild
* **2**: Moderate
* **3**: Severe
* **4**: Proliferative DR

## Project Structure

* `app.py`: Entry point for the API.
* `preprocessing.py`: Image manipulation and enhancement logic.
* `models/`: Directory for pre-trained weight files.
* `utils.py`: Helper functions for file handling and response formatting.

## License

MIT
