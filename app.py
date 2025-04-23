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
            return json.load(f)
    return []

# Save stories to JSON file
import time

# Save stories to JSON file
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
        new_story = {
            'timestamp': time.time(),
            'id': story_id,
            'title': title,
            'byline': byline,
            'text': text,
            'image': filename,
            'likes': 0,
            'comments': []
        }

        stories.append(new_story)
        save_stories(stories)

        return redirect(url_for('show_story', story_id=story_id, admin=request.args.get('admin')))

    return render_template_string(INDEX_TEMPLATE, stories=stories, admin=session.get('admin', False))

@app.route('/story/<story_id>', methods=['GET', 'POST'])
def show_story(story_id):
    admin_mode = session.get('admin', False)
    stories = load_stories()
    story = next((s for s in stories if s['id'] == story_id), None)
    if not story:
        abort(404)

    if request.method == 'POST':
        comment = request.form.get('comment', '').strip()
        if comment:
            story['comments'].append(comment)
            save_stories(stories)

    return render_template_string(STORY_TEMPLATE, story=story, admin=session.get('admin', False))

@app.route('/like/<story_id>', methods=['POST'])
def like_story(story_id):
    stories = load_stories()
    for story in stories:
        if story['id'] == story_id:
            story['likes'] += 1
            break
    save_stories(stories)
    return redirect(url_for('index'))

@app.route('/delete/<story_id>', methods=['POST'])
def delete_story(story_id):
    admin_mode = session.get('admin', False)
    stories = load_stories()
    story = next((s for s in stories if s['id'] == story_id), None)

    if not story:
        abort(404)

    if not admin_mode:
        return "Unauthorized: admin access required", 403

    stories = [s for s in stories if s['id'] != story_id]
    save_stories(stories)
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Flash Fiction Publisher</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 1rem; }
    input, textarea { width: 100%; padding: 0.5rem; margin-bottom: 1rem; }
    img { max-height: 200px; display: block; margin-bottom: 1rem; }
    .story-link { border: 1px solid #ccc; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>Publish Your Flash Fiction</h1>
  <form method="POST" enctype="multipart/form-data">
    <input name="title" placeholder="Story Title" required>
    <input name="byline" placeholder="Byline (e.g., Jane Doe)" required>
    <textarea name="text" placeholder="Write your story here (max 1,000 words)" rows="10" required></textarea>
    <input type="file" name="image" accept="image/*">
    <button type="submit">Publish</button>
  </form>

  <h2>Published Stories</h2>
  {% for story in stories %}
    <div class="story-link">
      <a href="{{ url_for('show_story', story_id=story.id) }}">
        <strong>{{ story.title }}</strong> by {{ story.byline }}
      </a>
      <form method="POST" action="{{ url_for('like_story', story_id=story.id) }}">
        <button type="submit">👍 Like ({{ story.likes }})</button>
      </form>
      {% if admin %}
        <form method="POST" action="{{ url_for('delete_story', story_id=story.id) }}?admin=secret-admin" style="margin-top:0.5rem">
          <button type="submit" onclick="return confirm('Delete this story?')">Delete</button>
        </form>
      {% endif %}
    </div>
  {% endfor %}
</body>
</html>
"""

STORY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>{{ story.title }}</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 1rem; }
    img { max-height: 300px; margin-bottom: 1rem; display: block; }
  </style>
  <script>
    function copyLink() {
      navigator.clipboard.writeText(window.location.href).then(() => alert('Link copied to clipboard!'));
    }
  </script>
</head>
<body>
  <h1>{{ story.title }}</h1>
  <p><em>By: {{ story.byline }}</em></p>
  {% if story.image %}
    <img src="{{ url_for('uploaded_file', filename=story.image) }}" alt="Story image">
  {% endif %}
  <p style="white-space: pre-wrap;">{{ story.text }}</p>
  <p><button onclick="copyLink()">Copy Link</button></p>
  <form method="POST" action="{{ url_for('like_story', story_id=story.id) }}">
    <button type="submit">👍 Like ({{ story.likes }})</button>
  </form>
  <h3>Comments</h3>
  <ul>
    {% for comment in story.comments %}
      <li>{{ comment }}</li>
    {% endfor %}
  </ul>
  <form method="POST">
    <textarea name="comment" placeholder="Leave a comment..." required></textarea>
    <button type="submit">Comment</button>
  </form>
  {% if admin %}
    <form method="POST" action="{{ url_for('delete_story', story_id=story.id) }}?admin=secret-admin">
      <button type="submit" onclick="return confirm('Delete this story?')">Delete</button>
    </form>
  {% endif %}
  <p><a href="/">← Back to all stories</a></p>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
