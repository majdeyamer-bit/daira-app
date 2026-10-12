from flask import Flask, request, jsonify, session, render_template_string, redirect
import json, os

app = Flask(__name__)
app.secret_key = "majdi-secret-123"

USERS_FILE="users.json"
MSGS_FILE="msgs.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(u):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(u, f, ensure_ascii=False, indent=2)

def load_msgs():
    if os.path.exists(MSGS_FILE):
        try:
            with open(MSGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_msgs(m):
    with open(MSGS_FILE, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

HTML="""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>الدائرة</title>
<style>body{font-family:system-ui;background:#0f172a;color:white;padding:20px}.card{background:#1e293b;padding:15px;border-radius:10px;margin:10px 0} input{padding:10px;width:70%;border-radius:5px;border:none} button{padding:10px 15px;background:#22c55e;border:none;border-radius:5px;cursor:pointer} #chat{height:300px;overflow-y:auto;background:#0f172a;border:1px solid #334155;padding:10px}</style>
</head><body>
<h2>🔒 الدائرة المغلقة</h2>
{% if not session.username %}
<div class="card"><h3>تسجيل دخول</h3>
<input id="u" placeholder="اسم المستخدم"><input id="f" placeholder="الاسم الكامل">
<button onclick="reg()">تسجيل</button><p id="st"></p></div>
{% else %}
<div class="card">مرحبا {{session.fullname}} - <a href="/logout" style="color:#f87171">خروج</a> {% if session.username=="مجدي" %} | <a href="/admin" style="color:yellow">الادمن</a>{% endif %}</div>
<div class="card"><div id="chat"></div><br>
<input id="msg" placeholder="اكتب..."><button onclick="send()">ارسال</button></div>
{% endif %}
<script>
function reg(){fetch('/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('u').value,fullname:document.getElementById('f').value})}).then(r=>r.json()).then(d=>{document.getElementById('st').innerText=d.msg; if(d.ok) location.reload()})}
function load(){fetch('/msgs').then(r=>r.json()).then(d=>{let c=document.getElementById('chat'); if(!c) return; c.innerHTML=d.map(m=>`<div><b>${m.user}:</b> ${m.text}</div>`).join(''); c.scrollTop=c.scrollHeight})}
function send(){let t=document.getElementById('msg').value; if(!t) return; fetch('/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})}).then(()=>{document.getElementById('msg').value=''; load()})}
setInterval(load,2000); load();
</script></body></html>
"""

@app.route("/")
def home(): return render_template_string(HTML)

@app.route("/register", methods=["POST"])
def register():
    d=request.json; u=d.get("username","").strip(); f=d.get("fullname",u).strip()
    if not u: return jsonify(msg="اكتب الاسم")
    users=load_users()
    if u not in users:
        users[u]={"fullname":f,"approved": (u=="مجدي")}
        save_users(users)
        if u=="مجدي":
            session["username"]=u; session["fullname"]=f
            return jsonify(msg="تم",ok=True)
        return jsonify(msg="انتظر موافقة الادمن")
    else:
        if not users[u].get("approved"): return jsonify(msg="انتظر موافقة الادمن")
        session["username"]=u; session["fullname"]=users[u]["fullname"]
        return jsonify(msg="تم",ok=True)

@app.route("/msgs")
def get_msgs(): return jsonify(load_msgs())

@app.route("/send", methods=["POST"])
def send_msg():
    if "username" not in session: return jsonify(msg="سجل دخول"),401
    users=load_users()
    if not users.get(session["username"],{}).get("approved"): return jsonify(msg="غير موافق"),403
    t=request.json.get("text","").strip()
    if not t: return jsonify(ok=True)
    m=load_msgs()
    m.append({"user":session.get("fullname"),"username":session.get("username"),"text":t})
    save_msgs(m)
    return jsonify(ok=True)

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

@app.route("/admin")
def admin():
    if session.get("username")!="مجدي": return "ممنوع"
    users=load_users(); h='<h2>لوحة الادمن</h2><a href="/">رجوع</a><br><br>'
    for k,v in users.items():
        if not v.get("approved"):
            h+=f'{k} ({v.get("fullname")}) <a href="/approve/{k}">[موافقة]</a><br>'
    if h=='<h2>لوحة الادمن</h2><a href="/">رجوع</a><br><br>': h+='لا يوجد طلبات'
    return h

@app.route("/approve/<u>")
def approve(u):
    if session.get("username")!="مجدي": return "ممنوع"
    users=load_users()
    if u in users:
        users[u]["approved"]=True
        save_users(users)
    return redirect("/admin")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
