from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson import ObjectId 

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456'  # Replace with your secret key
app.config['MONGO_URI'] = 'mongodb+srv://dhilippan28:Positive123@cluster0.uevgodk.mongodb.net/myDatabase?retryWrites=true&w=majority&appName=AtlasApp'  # Replace with your MongoDB URI
jwt = JWTManager(app)

# Connect to MongoDB using pymongo
client = MongoClient(app.config['MONGO_URI'])
db = client.get_database()

# User Collection
users = db['users']

# Template Collection
templates = db['templates']
db = client.get_default_database()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    password = data['password']

    if users.find_one({'email': email}):
        return jsonify({'message': 'Email already exists'}), 400

    hashed_password = generate_password_hash(password)
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': hashed_password
    }
    users.insert_one(user_data)

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']

    user = users.find_one({'email': email})
    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=str(user['_id']))
        return jsonify({'message': 'Login successful', 'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/template', methods=['POST'])
@jwt_required
def create_template():
    data = request.json
    template_name = data['template_name']
    subject = data['subject']
    body = data['body']
    user_id = get_jwt_identity()
    print(user_id)
    user = users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'message': 'User not found'}), 404

    template_data = {
        'template_name': template_name,
        'subject': subject,
        'body': body,
        'user_id': user_id
    }
    templates.insert_one(template_data)

    return jsonify({'message': 'Template created successfully'}), 201

@app.route('/templates', methods=['GET'])
@jwt_required
def get_templates():
    user_id = get_jwt_identity()

    user = users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user_templates = templates.find({'user_id': user_id})

    template_list = []
    for template in user_templates:
        template_data = {
            'template_name': template['template_name'],
            'subject': template['subject'],
            'body': template['body'],
            'template_id': str(template['_id'])  # Convert ObjectId to string
        }
        template_list.append(template_data)

    return jsonify({'templates': template_list}), 200

@app.route('/template/<string:template_id>', methods=['GET'])
@jwt_required
def get_template(template_id):
    user_id = get_jwt_identity()

    user = users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'message': 'User not found'}), 404

    template = templates.find_one({'_id': ObjectId(template_id), 'user_id': user_id})
    if not template:
        return jsonify({'message': 'Template not found or does not belong to the user'}), 404

    # Prepare the template data to be returned
    template_data = {
        'template_name': template['template_name'],
        'subject': template['subject'],
        'body': template['body']
    }

    return jsonify(template_data), 200

@app.route('/template/<string:template_id>', methods=['PUT'])
@jwt_required
def update_template(template_id):
    data = request.json
    template_name = data['template_name']
    subject = data['subject']
    body = data['body']
    user_id = get_jwt_identity()

    user = users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'message': 'User not found'}), 404

    template = templates.find_one({'_id': ObjectId(template_id), 'user_id': user_id})
    if not template:
        return jsonify({'message': 'Template not found or does not belong to the user'}), 404

    # Update the template data
    templates.update_one(
        {'_id': ObjectId(template_id)},
        {'$set': {'template_name': template_name, 'subject': subject, 'body': body}}
    )

    return jsonify({'message': 'Template updated successfully'}), 200


@app.route('/template/<string:template_id>', methods=['DELETE'])
@jwt_required
def delete_template(template_id):
    user_id = get_jwt_identity()

    user = users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'message': 'User not found'}), 404

    template = templates.find_one({'_id': ObjectId(template_id), 'user_id': user_id})
    if not template:
        return jsonify({'message': 'Template not found or does not belong to the user'}), 404

    # Delete the template
    templates.delete_one({'_id': ObjectId(template_id)})

    return jsonify({'message': 'Template deleted successfully'}), 200