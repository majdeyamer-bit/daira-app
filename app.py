from flask import Flask, request, jsonify, render_template_string, session, redirect
import json, os, time
app = Flask(__name__)
app.secret_key = "majdi-secret-123"
USERS_FILE="users.json"
MSGS_FILE="msgs.json"
def load_users():
    if os.path.exists(USERS_FILE):
        try: return json.load(open(USERS_FILE))
        except: return {}
    return {}
def save_users(u): json.dump(u, open(USERS_FILE,"w"), ensure_ascii=False)
def load_msgs():
    if os.path.exists(MSGS_FILE):
        try: return json.load(open(MSGS_FILE))
        except: return []
    return []
def save_msgs(m): json.dump(m, open(MSGS_FILE,"w"), ensure_ascii=False)
HTML="""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>الدائرة</title>
<style>body{font-family:system-ui;background:#0f172a;color:#fff;margin:0;padding:12px}.card{background:#1e293b;padding:15px;border-radius:12px;margin:10px 0}input,button{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:none}button{background:#22c55e;font-weight:bold}a{color:#38bdf8}</style></head><body>
<h2>🔒 الدائرة المغلقة</h2>
{% if not session.username %}
<div class="card"><h3>تسجيل دخول</h3>
<input id="u" placeholder="اسم المستخدم"><input id="f" placeholder="الاسم الكامل"><input id="p" placeholder="رقم الهاتف">
<button onclick="reg()">تسجيل</button></div>
{% else %}
<div class="card">مرحبا {{session.fullname}} - <a href="/logout">خروج</a> | <a href="https://instagram.com/m__s_6_8" target="_blank">📸 m__s_6_8</a> {% if session.username=='مجدي' %} | <a href="/admin">ادمن</a> {% endif %}</div>
<div class="card"><div id="chat" style="height:300px;overflow:auto;background:#0f172a;padding:8px"></div>
<input id="msg" placeholder="اكتب..."><button onclick="send()">ارسال</button></div>
{% endif %}
<script>
function reg(){fetch('/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('u').value,fullname:document.getElementById('f').value,phone:document.getElementById('p').value})}).then(r=>r.json()).then(d=>{alert(d.msg);location.reload()})}
function load(){fetch('/msgs').then(r=>r.json()).then(d=>{let c=document.getElementById('chat'); if(c) c.innerHTML=d.map(m=>'<div><b>'+m.user+':</b> '+m.text+'</div>').join('')})}
function send(){let t=document.getElementById('msg').value; if(!t) return; fetch('/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})}).then(()=>{document.getElementById('msg').value=''; load()})}
setInterval(load,2000); load();
</script></body></html>
"""
@app.route("/")
def home(): return render_template_string(HTML)
@app.route("/register", methods=["POST"])
def register():
    d=request.json; u=d.get("username","").strip()
    if not u: return jsonify(msg="اكتب الاسم")
    users=load_users()
    if u not in users:
        users[u]={"fullname":d.get("fullname"),"phone":d.get("phone"),"approved": False if u!="مجدي" else True}
        save_users(users)
        if u=="مجدي": session["username"]=u; session["fullname"]=users[u]["fullname"]; return jsonify(msg="تم تسجيل الادمن")
        return jsonify(msg="تم، انتظر موافقة الادمن")
    else:
        if not users[u]["approved"]: return jsonify(msg="حسابك قيد المراجعة")
        session["username"]=u; session["fullname"]=users[u]["fullname"]; return jsonify(msg="تم الدخول")
@app.route("/msgs")
def get_msgs(): return jsonify(load_msgs()[-50:])
@app.route("/send", methods=["POST"])
def send_msg():
    if "username" not in session: return jsonify(error="سجل اولا")
    users=load_users()
    if not users.get(session["username"],{}).get("approved"): return jsonify(error="غير موافق")
    t=request.json.get("text",""); m=load_msgs(); m.append({"user":session["username"],"text":t}); save_msgs(m); return jsonify(ok=True)
@app.route("/logout")
def logout(): session.clear(); return redirect("/")
@app.route("/admin")
def admin():
    if session.get("username")!="مجدي": return "ممنوع"
    users=load_users(); h="<h2>لوحة الادمن</h2><a href='/'>رجوع</a><br>"
    for k,v in users.items():
        if not v.get("approved"): h+=f"{k} <a href='/approve/{k}'>موافقة</a><br>"
    return h
@app.route("/approve/<u>")
def approve(u):
    if session.get("username")!="مجدي": return "ممنوع"
    users=load_users(); users[u]["approved"]=True; save_users(users); return redirect("/admin")
if __name__=="__main__": app.run(host="0.0.0.0",port=10000)
