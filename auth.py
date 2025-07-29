from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.get_database('retinopathy')
users_collection = db.users
tests_collection = db.tests

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        print("Received signup data:", data)  # Debug print
        
        # Check required fields
        required_fields = ['username', 'email', 'password', 'age']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'Missing required field: {field}'}), 400

        # Validate age
        try:
            age = int(data['age'])
            if age < 1 or age > 120:
                return jsonify({'message': 'Age must be between 1 and 120'}), 400
        except ValueError:
            return jsonify({'message': 'Invalid age format'}), 400

        # Check if username or email already exists
        if users_collection.find_one({'username': data['username']}):
            return jsonify({'message': 'Username already exists'}), 400
            
        if users_collection.find_one({'email': data['email']}):
            return jsonify({'message': 'Email already exists'}), 400

        # Create new user
        hashed_password = generate_password_hash(data['password'], method='sha256')
        
        new_user = {
            'username': data['username'],
            'email': data['email'],
            'password': hashed_password,
            'age': age,
            'test_count': 0,
            'tests': []
        }
        
        result = users_collection.insert_one(new_user)
        new_user['_id'] = str(result.inserted_id)
        
        # Create access token for immediate login
        access_token = create_access_token(
            identity=str(result.inserted_id),
            expires_delta=timedelta(days=1)
        )
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': {
                'id': str(result.inserted_id),
                'username': new_user['username'],
                'email': new_user['email'],
                'age': new_user['age'],
                'test_count': new_user['test_count']
            }
        }), 201
        
    except Exception as e:
        print("Error in signup:", str(e))  # Debug print
        return jsonify({'message': 'Error creating user', 'error': str(e)}), 500

@auth.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing email or password'}), 400

        user = users_collection.find_one({'email': data['email']})

        if not user or not check_password_hash(user['password'], data['password']):
            return jsonify({'message': 'Invalid email or password'}), 401

        access_token = create_access_token(
            identity=str(user['_id']),
            expires_delta=timedelta(days=1)
        )
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'age': user['age'],
                'test_count': user.get('test_count', 0)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Error during login', 'error': str(e)}), 500

@auth.route('/add-test', methods=['POST'])
@jwt_required()
def add_test():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({'message': 'No test data provided'}), 400

        # Create test record
        test_data = {
            'user_id': ObjectId(current_user_id),
            'date': data['date'],
            'result': data['result'],
            'confidence': data['confidence'],
            'status': data['status'],
            'recommendations': data['recommendations']
        }

        # Insert test into tests collection
        test_result = tests_collection.insert_one(test_data)

        # Update user's test count and add test reference
        users_collection.update_one(
            {'_id': ObjectId(current_user_id)},
            {
                '$inc': {'test_count': 1},
                '$push': {'tests': test_result.inserted_id}
            }
        )

        return jsonify({
            'message': 'Test added successfully',
            'test_id': str(test_result.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({'message': 'Error adding test', 'error': str(e)}), 500

@auth.route('/get-tests', methods=['GET'])
@jwt_required()
def get_tests():
    try:
        current_user_id = get_jwt_identity()
        
        # Get user's tests
        tests = list(tests_collection.find({'user_id': ObjectId(current_user_id)}))
        
        # Convert ObjectId to string for JSON serialization
        for test in tests:
            test['_id'] = str(test['_id'])
            test['user_id'] = str(test['user_id'])

        return jsonify({
            'tests': tests
        }), 200

    except Exception as e:
        return jsonify({'message': 'Error fetching tests', 'error': str(e)}), 500

@auth.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    try:
        current_user_id = get_jwt_identity()
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify({
            'message': 'Protected route',
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'age': user['age'],
                'test_count': user.get('test_count', 0)
            }
        })
    except Exception as e:
        return jsonify({'message': 'Error accessing protected route', 'error': str(e)}), 500
