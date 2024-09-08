# app.py

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
import random
import string
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app)  # Enable CORS

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')  # Path to your service account key
firebase_admin.initialize_app(cred)
db = firestore.client()

# Collection name in Firestore
EMAIL_COLLECTION = 'temp_emails'

def generate_random_email():
    domain = "coloruz.com"  # Replace with your domain
    prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{prefix}@{domain}"

@app.route('/')
def home():
    return render_template('index.html', email='generating...')

@app.route('/generate', methods=['POST'])
def generate_temp_email():
    email = generate_random_email()
    creation_time = datetime.utcnow()
    expiry_time = creation_time + timedelta(minutes=10)

    # Data to store
    email_data = {
        'email': email,
        'creation_time': creation_time.isoformat(),
        'expiry_time': expiry_time.isoformat()
    }

    # Use email as the document ID for uniqueness
    doc_ref = db.collection(EMAIL_COLLECTION).document(email)
    doc_ref.set(email_data)

    return jsonify({'email': email})

@app.route('/delete', methods=['POST'])
def delete_temp_email():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    doc_ref = db.collection(EMAIL_COLLECTION).document(email)
    doc = doc_ref.get()

    if doc.exists:
        doc_ref.delete()
        return jsonify({'message': 'Email deleted successfully'})
    else:
        return jsonify({'error': 'Email not found'}), 404

@app.route('/emails', methods=['GET'])
def get_emails():
    # Optional: Retrieve all emails (useful for admin purposes)
    emails = []
    docs = db.collection(EMAIL_COLLECTION).stream()
    for doc in docs:
        emails.append(doc.to_dict())
    return jsonify(emails)

# Optional: Endpoint to clean up expired emails
# You might want to set up a scheduled job for this
@app.route('/cleanup', methods=['POST'])
def cleanup_emails():
    now = datetime.utcnow().isoformat()
    emails = db.collection(EMAIL_COLLECTION).where('expiry_time', '<', now).stream()
    deleted = 0
    for email in emails:
        email.reference.delete()
        deleted += 1
    return jsonify({'deleted': deleted})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
