from flask import Flask, request, jsonify, render_template, redirect, session, send_from_directory
from google.cloud import storage
import google.generativeai as genai
import os
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure secret key

# Google Cloud Storage and Gemini AI configuration
bucket_name = "your-bucket-name"  # Replace with your Cloud Storage bucket name
storage_client = storage.Client()
genai.configure(api_key="your-gemini-api-key")  # Replace with your Gemini API key

# Ensure the local 'files' directory exists
os.makedirs('files', exist_ok=True)

@app.route('/')
def index():
    """
    Render the main page with the image upload form and list of uploaded images.
    """
    user_id = session.get('user')
    if not user_id:
        return redirect('/login')

    # Fetch and display uploaded images
    images = get_user_images(user_id)
    return render_template('index.html', images=images, user_id=user_id)

@app.route('/upload', methods=['POST'])
def upload():
    """
    Handle image uploads, generate metadata using Gemini AI, and save files to Cloud Storage.
    """
    user_id = session.get('user')
    if not user_id:
        return redirect('/login')

    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400

    # Save the file locally temporarily
    local_path = os.path.join('files', file.filename)
    file.save(local_path)

    # Upload the file to Google Cloud Storage
    blob = storage_client.bucket(bucket_name).blob(f"{user_id}/{file.filename}")
    blob.upload_from_filename(local_path)

    # Generate metadata using Gemini AI
    try:
        response = genai.generate_text(prompt=f"Describe the image {file.filename}")
        metadata = {
            "title": response.candidates[0].output,
            "description": response.candidates[0].output
        }
    except Exception as e:
        metadata = {
            "title": "No title generated",
            "description": "No description generated"
        }

    # Save metadata as a JSON file in Cloud Storage
    metadata_blob = storage_client.bucket(bucket_name).blob(f"{user_id}/{file.filename}.json")
    metadata_blob.upload_from_string(json.dumps(metadata), content_type='application/json')

    # Clean up the local file
    os.remove(local_path)

    return redirect('/')

@app.route('/get-images')
def get_images():
    """
    Return a list of uploaded images for the current user.
    """
    user_id = session.get('user')
    if not user_id:
        return jsonify([])

    # List images from Cloud Storage
    blobs = storage_client.list_blobs(bucket_name, prefix=f"{user_id}/")
    images = []
    for blob in blobs:
        if blob.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            images.append({
                "filename": blob.name.split('/')[-1],
                "title": blob.name.split('/')[-1]  # Fetch the title from metadata if needed
            })
    return jsonify(images)

@app.route('/files/<filename>')
def get_file(filename):
    """
    Serve uploaded images from the local filesystem.
    """
    return send_from_directory('files', filename)

@app.route('/view/<filename>')
def view_file(filename):
    """
    Display the image and its metadata.
    """
    user_id = session.get('user')
    if not user_id:
        return redirect('/login')

    # Fetch metadata from Cloud Storage
    metadata_blob = storage_client.bucket(bucket_name).blob(f"{user_id}/{filename}.json")
    if metadata_blob.exists():
        metadata = json.loads(metadata_blob.download_as_text())
    else:
        metadata = {
            "title": "No title available",
            "description": "No description available"
        }

    return render_template('view.html', filename=filename, title=metadata['title'], description=metadata['description'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Simulate user authentication (replace with Firebase or another auth system)
        session['user'] = email
        return redirect('/')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Handle user logout.
    """
    session.pop('user', None)
    return redirect('/login')

def get_user_images(user_id):
    """
    Helper function to fetch uploaded images for a specific user.
    """
    blobs = storage_client.list_blobs(bucket_name, prefix=f"{user_id}/")
    images = []
    for blob in blobs:
        if blob.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            images.append({
                "filename": blob.name.split('/')[-1],
                "title": blob.name.split('/')[-1]  # Fetch the title from metadata if needed
            })
    return images

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)