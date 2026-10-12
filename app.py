from flask import Flask, render_template, request, jsonify, session, send_from_directory
import json, os, time, base64
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "majdi-secret-123"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 # 20MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

USERS_FILE="users.json"
MSGS_FILE="msgs.json"
ALLOWED_IMAGES={'png','jpg','jpeg','gif','webp'}
ALLOWED_AUDIO={'mp3','wav','ogg','m4a','mp4','webm','aac','3gp'}

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}
def save_users(d):
    with open(USERS_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
def load_msgs():
    if os.path.exists(MSGS_FILE):
        try:
            with open(MSGS_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: return []
    return []
def save_msgs(d):
    with open(MSGS_FILE,"w",encoding="utf-8") as f: json.dump(d,f[-300:],ensure_ascii=False,indent=2)

def allowed_file(name, types): return '.' in name and name.rsplit('.',1)[1].lower() in types

@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    data=request.get_json()
    username=data.get("username","").strip()
    if not username: return jsonify({"error":"اكتب اسمك"}),400
    users=load_users()
    is_admin = len(users)==0
    if username not in users:
        users[username] = {"is_admin": is_admin, "banned": False, "joined": time.time()}
        save_users(users)
    session["username"]=username
    return jsonify({"ok":True,"is_admin": users[username].get("is_admin")})

@app.route("/api/messages")
def get_messages(): return jsonify(load_msgs())

@app.route("/api/send", methods=["POST"])
def send():
    if "username" not in session: return jsonify({"error":"login"}),401
    username=session["username"]
    users=load_users()
    if users.get(username,{}).get("banned"): return jsonify({"error":"مطرود"}),403
    data=request.get_json()
    text=data.get("text","").strip()
    if not text: return jsonify({"error":"فاضي"}),400
    msgs=load_msgs()
    msgs.append({"id": int(time.time()*1000), "user": username, "text": text, "type":"text", "time": datetime.now().strftime("%H:%M"), "reactions": {}, "is_admin": users.get(username,{}).get("is_admin",False)})
    save_msgs(msgs)
    return jsonify({"ok":True})

# --- رفع صور + صوتيات ---
@app.route("/api/upload", methods=["POST"])
def upload():
    if "username" not in session: return jsonify({"error":"login"}),401
    username=session["username"]
    users=load_users()
    if users.get(username,{}).get("banned"): return jsonify({"error":"مطرود"}),403
    if 'file' not in request.files: return jsonify({"error":"مفيش ملف"}),400
    file=request.files['file']
    if file.filename=='' : return jsonify({"error":"مفيش ملف"}),400

    ext=file.filename.rsplit('.',1)[1].lower() if '.' in file.filename else ''
    if ext in ALLOWED_IMAGES: ftype='image'
    elif ext in ALLOWED_AUDIO: ftype='audio'
    else: return jsonify({"error":"نوع الملف مش مدعوم، صور و صوتيات بس"}),400

    filename=f"{int(time.time()*1000)}_{secure_filename(file.filename)}"
    path=os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    msgs=load_msgs()
    msgs.append({
        "id": int(time.time()*1000), "user": username, "text": f"/{app.config['UPLOAD_FOLDER']}/{filename}",
        "type": ftype, "filename": file.filename, "time": datetime.now().strftime("%H:%M"),
        "reactions": {}, "is_admin": users.get(username,{}).get("is_admin",False)
    })
    save_msgs(msgs)
    return jsonify({"ok":True, "url": f"/{app.config['UPLOAD_FOLDER']}/{filename}", "type":ftype})

@app.route('/static/uploads/<filename>')
def uploaded_file(filename): return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- مسح + طرد + رياكشن ---
@app.route("/api/delete/<int:msg_id>", methods=["DELETE"])
def delete_msg(msg_id):
    if "username" not in session: return jsonify({"error":"login"}),401
    username=session["username"]; users=load_users(); me=users.get(username,{})
    msgs=load_msgs()
    for m in msgs:
        if m["id"]==msg_id:
            if m["user"]==username or me.get("is_admin"):
                save_msgs([x for x in msgs if x["id"]!=msg_id]); return jsonify({"ok":True})
            else: return jsonify({"error":"مش مسموح"}),403
    return jsonify({"error":"not found"}),404

@app.route("/api/kick", methods=["POST"])
def kick():
    if "username" not in session: return jsonify({"error":"login"}),401
    users=load_users()
    if not users.get(session["username"],{}).get("is_admin"): return jsonify({"error":"مش ادمن"}),403
    target=request.get_json().get("username")
    if target in users and target!=session["username"]:
        users[target]["banned"]=True; save_users(users); return jsonify({"ok":True})
    return jsonify({"error":"not found"}),404

@app.route("/api/react", methods=["POST"])
def react():
    if "username" not in session: return jsonify({"error":"login"}),401
    username=session["username"]; data=request.get_json(); msg_id=data.get("msg_id"); emoji=data.get("emoji")
    msgs=load_msgs()
    for m in msgs:
        if m["id"]==msg_id:
            if emoji not in m["reactions"]: m["reactions"][emoji]=[]
            if username in m["reactions"][emoji]: m["reactions"][emoji].remove(username)
            else: m["reactions"][emoji].append(username)
            save_msgs(msgs); return jsonify({"ok":True})
    return jsonify({"error":"not found"}),404

@app.route("/api/users")
def list_users(): return jsonify(load_users())

if __name__=="__main__": app.run(host="0.0.0.0",port=10000)
