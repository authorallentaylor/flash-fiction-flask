from flask import Flask, request, render_template_string, redirect, url_for, send_from_directory, abort, jsonify, session
import os
import json
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

STORY_FILE = 'stories.json'
ADMIN_KEY = 'secret-admin'  # Change this to something secure

# Load stories from JSON file
def load_stories():
    if os.path.exists(STORY_FILE):
        with open(STORY_FILE, 'r') as f:
            stories = json.load(f)
        changed = False
        for story in stories:
            if 'timestamp' not in story:
                story['timestamp'] = time.time()
                changed = True
            if 'likes' not in story:
                story['likes'] = 0
                changed = True
            if 'comments' not in story:
                story['comments'] = []
                changed = True
        if changed:
            save_stories(stories)
        return stories
    return []

# Save stories to JSON file
import time

def save_stories(stories):
    with open(STORY_FILE, 'w') as f:
        json.dump(stories, f, indent=2)

@app.route('/', methods=['GET', 'POST'])
def index():
    stories = load_stories()
    if request.args.get('admin') == ADMIN_KEY:
        session['admin'] = True
    admin_mode = session.get('admin', False)

    for story in stories:
        if 'timestamp' not in story:
            story['timestamp'] = time.time()
    save_stories(stories)

    cutoff = time.time() - 120 * 24 * 60 * 60
    stories = [s for s in stories if s['timestamp'] >= cutoff]
    stories = load_stories()
    stories = sorted(stories, key=lambda x: x['id'], reverse=True)

    if request.method == 'POST':
        title = request.form['title']
        byline = request.form['byline']
        text = request.form['text']

        image_file = request.files.get('image')

        word_count = len(text.strip().split())
        if word_count > 1000:
            return "Error: Story must be 1,000 words or less.", 400

        filename = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        story_id = str(uuid.uuid4())[:8]
        edit_code = str(uuid.uuid4())[:8]
        new_story = {
            'timestamp': time.time(),
            'id': story_id,
            'title': title,
            'byline': byline,
            'text': text,
            'image': filename,
            'likes': 0,
            'comments': [],
            'edit_code': edit_code
        }

        stories.append(new_story)
        save_stories(stories)
        print(f"New story published: {title} by {byline}")

        return redirect(url_for('show_story', story_id=story_id, admin=request.args.get('admin')))

    return render_template_string(INDEX_TEMPLATE, stories=stories, admin=session.get('admin', False))

# ... the rest of the code remains unchanged ...
