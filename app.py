import os, json, uuid
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "daira-secret-2024-majdi-fixed-key" # مفتاح ثابت باش معاش يطردك
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

USERS_FILE = 'users.json'
MSGS_FILE = 'msgs.json'

def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE,'r',encoding='utf-8') as f: return json.load(f)
    except: pass
    return {}

def save_users(u):
    with open(USERS_FILE,'w',encoding='utf-8') as f: json.dump(u,f,ensure_ascii=False,indent=2)

def load_msgs():
    try:
        if os.path.exists(MSGS_FILE):
            with open(MSGS_FILE,'r',encoding='utf-8') as f: return json.load(f)
    except: pass
    return []

def save_msgs(m):
    with open(MSGS_FILE,'w',encoding='utf-8') as f: json.dump(m[-300:],f,ensure_ascii=False,indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    name = data.get('username','').strip()
    if not name: return jsonify({'ok':False,'error':'اكتب اسمك'})
    users = load_users()
    if name not in users:
        users[name] = {'banned':False, 'is_admin': len(users)==0}
        save_users(users)
    if users[name].get('banned'): return jsonify({'ok':False,'error':'تم حظرك 🚫'})
    session['username'] = name
    session.permanent = True
    return jsonify({'ok':True,'username':name,'is_admin':users[name].get('is_admin',False)})

@app.route('/api/messages')
def get_messages():
    return jsonify(load_msgs())

@app.route('/api/send', methods=['POST'])
def send():
    if 'username' not in session: return jsonify({'ok':False,'error':'login'}), 401
    users = load_users()
    if users.get(session['username'],{}).get('banned'): return jsonify({'ok':False,'error':'banned'}), 403
    data = request.json
    text = data.get('text','').strip()
    if not text: return jsonify({'ok':False})
    msgs = load_msgs()
    msgs.append({
        'id': str(uuid.uuid4()),
        'user': session['username'],
        'text': text,
        'time': datetime.now().strftime('%H:%M'),
        'type': 'text',
        'reactions': {}
    })
    save_msgs(msgs)
    return jsonify({'ok':True})

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'username' not in session: return jsonify({'ok':False}), 401
    if 'file' not in request.files: return jsonify({'ok':False})
    file = request.files['file']
    if file.filename == '': return jsonify({'ok':False})
    ext = file.filename.rsplit('.',1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    msgs = load_msgs()
    ftype = 'image' if ext in ['jpg','jpeg','png','gif','webp'] else 'voice' if ext in ['webm','mp3','wav','ogg','m4a'] else 'file'
    msgs.append({
        'id': str(uuid.uuid4()),
        'user': session['username'],
        'text': f"/{path}",
        'time': datetime.now().strftime('%H:%M'),
        'type': ftype,
        'reactions': {}
    })
    save_msgs(msgs)
    return jsonify({'ok':True, 'url': f"/{path}"})

@app.route('/api/react', methods=['POST'])
def react():
    if 'username' not in session: return jsonify({'ok':False}), 401
    data = request.json
    mid = data.get('id'); emoji = data.get('emoji')
    msgs = load_msgs()
    for m in msgs:
        if m['id']==mid:
            if 'reactions' not in m: m['reactions']={}
            if emoji not in m['reactions']: m['reactions'][emoji]=[]
            if session['username'] in m['reactions'][emoji]:
                m['reactions'][emoji].remove(session['username'])
            else:
                m['reactions'][emoji].append(session['username'])
            break
    save_msgs(msgs)
    return jsonify({'ok':True})

@app.route('/api/delete', methods=['POST'])
def delete_msg():
    if 'username' not in session: return jsonify({'ok':False}), 401
    data = request.json
    mid = data.get('id')
    users = load_users()
    is_admin = users.get(session['username'],{}).get('is_admin',False)
    msgs = load_msgs()
    msgs = [m for m in msgs if not (m['id']==mid and (m['user']==session['username'] or is_admin))]
    save_msgs(msgs)
    return jsonify({'ok':True})

@app.route('/api/ban', methods=['POST'])
def ban():
    if 'username' not in session: return jsonify({'ok':False}), 401
    users = load_users()
    if not users.get(session['username'],{}).get('is_admin'): return jsonify({'ok':False}), 403
    target = request.json.get('username')
    if target in users and target!= session['username']:
        users[target]['banned']=True
        save_users(users)
    return jsonify({'ok':True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
