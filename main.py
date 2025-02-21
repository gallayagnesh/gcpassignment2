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

def generate_metadata(image_path):
    """Uses Gemini AI to generate a title and description correctly."""
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Read the image in binary format
    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    # Send proper request to AI
    prompt = {
        "role": "user",
        "parts": [
            "Analyze this image and generate a short title and description in JSON format.",
            {"image": image_data}
        ]
    }

    try:
        response = model.start_chat(history=[prompt]).send_message("")
        
        # Debugging log (Check Cloud Run logs)
        print(f"AI Response: {response.text}")

        # Ensure response is valid JSON
        metadata = json.loads(response.text)
        title = metadata.get('title', 'Untitled')
        description = metadata.get('description', 'No description available')

    except Exception as e:
        print(f"Error in AI response: {str(e)}")
        title = "Untitled"
        description = "No description available"

    return title, description


@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')

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
        print(f"AI Generated -> Title: {title}, Description: {description}")

        return render_template('view.html', filename=filename, title=title, description=description)

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return "Error processing image", 500

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
