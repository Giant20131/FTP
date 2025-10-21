from flask import Flask, request, send_from_directory, render_template_string, jsonify, redirect, url_for, session
import os

# ---------- CONFIG ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PASSWORD = "secret123"  # Change this
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "super_secret_key_123"  # for session handling

# ---------- HTML ----------
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Neon FTP Chat</title>
<style>
body {
  background: radial-gradient(circle at top left, #001, #012, #023);
  font-family: Poppins, sans-serif;
  color: #00ffff;
  margin: 0; display: flex; flex-direction: column; align-items: center;
}
.chat-box {
  width: 90%; max-width: 500px; height: 80vh;
  overflow-y: auto; border-radius: 15px; border: 2px solid #0ff;
  background: rgba(0,0,30,0.6); box-shadow: 0 0 20px #00ffff55; margin-top: 20px;
}
.bubble { margin: 10px; padding: 12px 16px; border-radius: 20px;
  display: inline-block; position: relative; word-wrap: break-word;
}
.received { background: #111122; float: left; clear: both; }
.delete-btn {
  position: absolute; top: -6px; right: -6px; border: none;
  background: rgba(255,0,0,0.6); color: white; border-radius: 50%;
  width: 22px; height: 22px; cursor: pointer; display: none;
}
.bubble:hover .delete-btn { display: block; }
.upload-bar {
  width: 90%; max-width: 500px; display: flex; justify-content: space-between;
  align-items: center; padding: 10px; background: rgba(10,10,30,0.9);
  border-top: 2px solid #0ff5; border-radius: 0 0 15px 15px;
}
input[type=file] { display: none; }
.upload-btn { font-size: 1.6em; cursor: pointer; transition: 0.3s; }
.upload-btn:hover { transform: scale(1.2); }
.progress { width: 90%; max-width: 500px; height: 5px;
  background: rgba(255,255,255,0.1); border-radius: 10px; margin-top: 5px;
}
.bar { height: 100%; width: 0%; background: #00ffff; transition: width 0.2s; }
.login-box {
  width: 300px; text-align: center; margin-top: 100px;
  background: rgba(0,0,30,0.8); border: 2px solid #0ff; border-radius: 10px; padding: 20px;
}
.login-box input[type=password], .login-box input[type=submit] {
  width: 80%; margin: 8px 0; padding: 8px; border-radius: 8px; border: 1px solid #00ffff;
  background: rgba(0,0,0,0.2); color: #00ffff; outline: none;
}
.login-box input[type=submit]:hover { background: #00ffff; color: #000; cursor: pointer; }
.logout {
  margin-top: 10px; color: #00ffff; background: none; border: 1px solid #00ffff;
  padding: 6px 12px; border-radius: 8px; cursor: pointer;
}
.logout:hover { background: #00ffff; color: #000; }
a { color: #00ffff; text-decoration: none; }
</style>
</head>
<body>
{% if not authed %}
  <div class="login-box">
    <h2>Login</h2>
    <form method="POST" action="/login">
      <input type="password" name="password" placeholder="Enter Password" required><br>
      <input type="submit" value="Login">
    </form>
  </div>
{% else %}
  <div class="chat-box" id="chat"></div>
  <div class="upload-bar">
    <label for="file" class="upload-btn">📎</label>
    <input type="file" id="file" />
  </div>
  <div class="progress"><div class="bar" id="bar"></div></div>
  <form action="/logout" method="POST"><button class="logout">Logout</button></form>

  <script>
  const fileInput = document.getElementById('file');
  const chat = document.getElementById('chat');
  const bar = document.getElementById('bar');

  async function loadFiles() {
    const res = await fetch('/files');
    if(res.status === 401) { location.href='/'; return; }
    const files = await res.json();
    chat.innerHTML = '';
    if (files.length === 0)
      chat.innerHTML = '<div class="bubble received">No files yet. Upload one!</div>';
    files.forEach(f => {
      const div = document.createElement('div');
      div.className = 'bubble received';
      div.innerHTML = '📄 <a href="/uploads/'+f+'" download>'+f+'</a>' +
        '<button class="delete-btn" onclick="deleteFile(\\''+f+'\\')">✖</button>';
      chat.appendChild(div);
    });
    chat.scrollTop = chat.scrollHeight;
  }

  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload');
    xhr.upload.addEventListener('progress', e=>{
      if(e.lengthComputable){ bar.style.width=(e.loaded/e.total*100)+'%'; }
    });
    xhr.onload = ()=>{ bar.style.width='0%'; loadFiles(); };
    xhr.send(formData);
  });

  async function deleteFile(name) {
    if (!confirm('Delete '+name+'?')) return;
    await fetch('/delete/'+name, {method:'DELETE'});
    loadFiles();
  }

  setInterval(loadFiles, 5000);
  loadFiles();
  </script>
{% endif %}
</body>
</html>
"""

# ---------- ROUTES ----------
@app.route('/')
def home():
    if session.get("authed"):
        return render_template_string(HTML, authed=True)
    return render_template_string(HTML, authed=False)

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get('password')
    if pw == PASSWORD:
        session["authed"] = True
        return redirect(url_for('home'))
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/files')
def list_files():
    if not session.get("authed"):
        return 'Unauthorized', 401
    return jsonify(sorted(os.listdir(UPLOAD_FOLDER)))

@app.route('/upload', methods=['POST'])
def upload():
    if not session.get("authed"):
        return 'Unauthorized', 401
    f = request.files['file']
    if f:
        f.save(os.path.join(UPLOAD_FOLDER, f.filename))
    return '', 200

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    if not session.get("authed"):
        return 'Unauthorized', 401
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    if not session.get("authed"):
        return 'Unauthorized', 401
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
