import os
import json
from flask import Flask, request, render_template, redirect, session, send_from_directory
from google.cloud import storage
import google.generativeai as genai
import pyrebase

app = Flask(__name__)
app.secret_key = 'saipranaygcpassignment2'

# Configure Firebase
firebaseConfig = {
    "apiKey": "AIzaSyBxoqEroPT5ZQGtQ9xhkP-B8eCmMrj7tk8",
    "authDomain": "gcpassignment-f605d.firebaseapp.com",
    "databaseURL": "https://gcpassignment-f605d-default-rtdb.firebaseio.com",
    "projectId": "gcpassignment-f605d",
    "storageBucket": "gcpassignment2-csbucket"
}
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Configure Google Cloud Storage
storage_client = storage.Client()
bucket_name = "gcpassignment2-csbucket"

# Configure Google Gemini AI
genai.configure(api_key="AIzaSyABY4oVvH7JrxpA70rv0vhlWLJ5WjAVjoI")

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect('/login')

    try:
        file = request.files['image']
        filename = file.filename
        file.save(filename)

        # Generate metadata
        title, description = generate_metadata(filename)

        # Debugging logs
        print(f"Uploaded: {filename}, Title: {title}, Description: {description}")

        return render_template('view.html', filename=filename, title=title, description=description)

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return "Error processing image", 500

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

    # Generate metadata
    title, description = generate_metadata(filename)
    
    return render_template('view.html', filename=filename, title=title, description=description)

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
