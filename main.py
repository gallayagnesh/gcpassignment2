import os
import json
from flask import Flask, request, render_template, redirect, session, send_from_directory
from google.cloud import storage
import google.generativeai as genai
import pyrebase

app = Flask(__name__,template_folder='templates')
app.secret_key = 'saipranaygcpassignment2'

# Configure Firebase
firebaseConfig = {
    "apiKey": "AIzaSyBxoqEroPT5ZQGtQ9xhkP-B8eCmMrj7tk8",
    "authDomain": "gcpassignment-f605d.firebaseapp.com",
    "databaseURL": "https://gcpassignment-f605d-default-rtdb.firebaseio.com",
    "projectId": "gcpassignment-f605d",
    "storageBucket": "https://console.cloud.google.com/storage/browser/gcpassignment2-csbucket"
}
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Configure Google Cloud Storage
storage_client = storage.Client()
bucket_name = "gcpassignment2-csbucket"

# Configure Google Gemini AI
genai.configure(api_key="AIzaSyABY4oVvH7JrxpA70rv0vhlWLJ5WjAVjoI")

def upload_to_gcs(bucket_name, source_file, destination_blob):
    """Uploads a file to Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)

def generate_metadata(image_path):
    """Uses Gemini AI to generate title and description."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"Describe the image: {image_path}")
    return response.text

@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect('/login')
    
    file = request.files['image']
    filename = file.filename
    file.save(filename)

    # Upload to GCS
    upload_to_gcs(bucket_name, filename, filename)

    # Generate metadata
    metadata = generate_metadata(filename)
    with open(f"{filename}.txt", "w") as f:
        f.write(metadata)
    
    upload_to_gcs(bucket_name, f"{filename}.txt", f"{filename}.txt")

    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = user['localId']
            return redirect('/')
        except:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
