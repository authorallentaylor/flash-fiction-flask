from flask import Flask, request, render_template_string, redirect, url_for, send_from_directory, abort, jsonify, session
import os
import json
import uuid
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

STORY_FILE = 'stories.json'
ADMIN_KEY = 'secret-admin'  # Change this to something secure

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Write a Flash Fiction Story</title>
</head>
<body>
  <h1>Submit Your Flash Fiction</h1>
  <form method=\"POST\" enctype=\"multipart/form-data\">
    <p><input name=\"title\" placeholder=\"Story Title\" required></p>
    <p><input name=\"byline\" placeholder=\"Your Name\" required></p>
    <p><textarea name=\"text\" placeholder=\"Write your story...\" rows=\"10\" cols=\"60\" required></textarea></p>
    <p><input type=\"file\" name=\"image\"></p>
    <p><button type=\"submit\">Save Story</button></p>
  </form>
  <hr>
  <h2>Published Stories</h2>
  <ul>
    {% for story in stories %}
      <li><a href=\"{{ url_for('show_story', story_id=story.id) }}\">{{ story.title }}</a> by {{ story.byline }}</li>
    {% endfor %}
  </ul>
</body>
</html>
"""

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

    active_stories = [s for s in stories if s['timestamp'] >= cutoff]
    stories = sorted(active_stories, key=lambda x: x['timestamp'], reverse=True)
    return render_template_string(INDEX_TEMPLATE, stories=stories, admin=session.get('admin', False))

@app.route('/story/<story_id>', methods=['GET'])
def show_story(story_id):
    stories = load_stories()
    story = next((s for s in stories if s['id'] == story_id), None)
    if not story:
        abort(404)
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>{{ story.title }}</title>
      <style>
        body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 1rem; }
        .button { font-size: 1rem; padding: 0.5rem 1rem; margin: 0.25rem; border: 2px solid silver; background: black; color: white; cursor: pointer; display: inline-block; }
        .comment-box { width: 100%; height: 100px; }
      </style>
    </head>
    <body>
      <h1>{{ story.title }}</h1>
      <p><em>by {{ story.byline }}</em></p>
      <p>{{ story.text }}</p>

      <div>
        <button class="button" onclick="navigator.clipboard.writeText(window.location.href)">Copy Link</button>
        <a href="https://twitter.com/intent/tweet?url={{ request.url }}" target="_blank" class="button">Share to X</a>
      </div>

      <div>
        <form method="POST" action="/like/{{ story.id }}">
          <button type="submit" class="button">👍 Like ({{ story.likes }})</button>
        </form>
      </div>

      <h2>Comments</h2>
      <ul>
        {% for comment in story.comments %}
          <li>{{ comment }}</li>
        {% endfor %}
      </ul>

      <form method="POST" action="/comment/{{ story.id }}">
        <textarea name="comment" placeholder="Leave a comment..." class="comment-box"></textarea><br>
        <button type="submit" class="button">Comment</button>
      </form>

      <p><a href="/">← Back to all stories</a></p>
    </body>
    </html>
    """, story=story)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
