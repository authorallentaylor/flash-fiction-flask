from flask import Flask, request, render_template_string, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

stories = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Flash Fiction App</title>
  <style>
    body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 1rem; }
    input, textarea { width: 100%; padding: 0.5rem; margin-bottom: 1rem; }
    img { max-height: 200px; margin-bottom: 1rem; }
    button { padding: 0.5rem 1rem; margin-right: 0.5rem; }
    .story { border: 1px solid #ccc; padding: 1rem; margin-bottom: 2rem; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>Flash Fiction Writer</h1>
  <form method="POST" enctype="multipart/form-data">
    <input name="title" placeholder="Story Title" required />
    <input name="byline" placeholder="Byline (e.g., Jane Doe)" required />
    <textarea name="text" rows="10" placeholder="Write your story here (max 1,000 words)" required></textarea>
    <input type="file" name="image" accept="image/*" />
    <button type="submit">Save Story</button>
  </form>

  <h2>My Stories</h2>
  {% if stories %}
    {% for story in stories %}
      <div class="story">
        <h3>{{ story.title }}</h3>
        <p><em>By: {{ story.byline }}</em></p>
        {% if story.image %}
          <img src="{{ url_for('uploaded_file', filename=story.image) }}" alt="Story image" />
        {% endif %}
        <p style="white-space: pre-wrap;">{{ story.text }}</p>
        <button onclick="copyLink('{{ loop.index0 }}')">Copy Link</button>
        <a href="https://twitter.com/intent/tweet?text={{ story.title|urlencode }}%0A%0A{{ story.text|urlencode }}%0A%0ABy: {{ story.byline|urlencode }}" target="_blank">
          <button>Share to X</button>
        </a>
      </div>
    {% endfor %}
  {% else %}
    <p>No stories yet.</p>
  {% endif %}

<script>
  function copyLink(index) {
    const url = window.location.href.split("#")[0] + "#story-" + index;
    navigator.clipboard.writeText(url).then(() => alert("Link copied to clipboard!"));
  }
</script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
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
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        stories.append({
            'title': title,
            'byline': byline,
            'text': text,
            'image': filename
        })
        return redirect(url_for('index'))

    return render_template_string(HTML_TEMPLATE, stories=stories)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

