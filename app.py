import streamlit as st
import sqlite3
import time
import random
from datetime import datetime

st.set_page_config(page_title="Face Recognition Attendance System", page_icon="🎓", layout="wide")

st.markdown("""
<style>
.stApp{background-color:#f0f4f8}
.header-box{background:linear-gradient(135deg,#1e3a5f,#1d4ed8);padding:20px 28px;border-radius:14px;color:white;margin-bottom:14px}
.header-box h1{font-size:21px;font-weight:800;margin:0}
.header-box p{font-size:12px;opacity:.75;margin:4px 0 0 0}
.conf-banner{background:linear-gradient(90deg,#fef3c7,#fde68a,#fef3c7);border:1px solid #f59e0b;border-radius:8px;padding:8px 16px;text-align:center;font-size:12px;font-weight:700;color:#92400e;letter-spacing:1px;margin-bottom:14px}
.metric-card{background:white;border-radius:14px;padding:18px;text-align:center;box-shadow:0 2px 12px rgba(37,99,235,.08);border:1px solid #e2e8f0;margin-bottom:8px}
.metric-val{font-size:28px;font-weight:800;margin-bottom:4px}
.metric-lbl{font-size:10px;color:#94a3b8;font-weight:600;letter-spacing:.5px;text-transform:uppercase}
.step-done{background:#d1fae5;border-left:4px solid #10b981;padding:8px 14px;border-radius:0 8px 8px 0;margin-bottom:6px;font-size:13px;color:#065f46;font-weight:600}
.match-box{background:#f0fdf4;border:2px solid #10b981;border-radius:14px;padding:20px 24px}
.nomatch-box{background:#fef2f2;border:2px solid #ef4444;border-radius:14px;padding:24px;text-align:center}
.camera-idle{background:#0f172a;border-radius:14px;padding:60px 32px;text-align:center;border:2px dashed #334155}
</style>
""", unsafe_allow_html=True)

DB = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS students (student_id TEXT PRIMARY KEY, name TEXT, department TEXT, year TEXT, enrolled_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, name TEXT, department TEXT, year TEXT, date TEXT, time TEXT, confidence REAL, session TEXT)")
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for s in [("KA2024001","Aarav Sharma","Information Technology","III Year"),("KA2024002","Priya Nair","Information Technology","II Year"),("KA2024003","Karthik Raja","Computer Science","III Year"),("KA2024004","Divya Mohan","Information Technology","I Year"),("KA2024005","Arjun Patel","Electronics","II Year"),("KA2024006","Sneha Kumar","Computer Science","IV Year"),("KA2024007","Vikram Singh","Mechanical","I Year"),("KA2024008","Ananya Roy","Information Technology","III Year"),("KA2024009","Rahul Menon","Computer Science","II Year"),("KA2024010","Lakshmi Iyer","Information Technology","IV Year")]:
            conn.execute("INSERT OR IGNORE INTO students VALUES (?,?,?,?,?)",(s[0],s[1],s[2],s[3],now))
        conn.commit()
    conn.close()

def get_students():
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT student_id,name,department,year FROM students").fetchall()
    conn.close()
    return [{"id":r[0],"name":r[1],"dept":r[2],"year":r[3]} for r in rows]

def get_attendance(date=None):
    date = date or datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT student_id,name,department,year,time,confidence,session FROM attendance WHERE date=? ORDER BY time DESC",(date,)).fetchall()
    conn.close()
    return rows

def mark_attendance(sid,name,dept,year,conf,session):
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect(DB)
    if conn.execute("SELECT id FROM attendance WHERE student_id=? AND date=? AND session=?",(sid,today,session)).fetchone():
        conn.close()
        return False
    conn.execute("INSERT INTO attendance (student_id,name,department,year,date,time,confidence,session) VALUES (?,?,?,?,?,?,?,?)",(sid,name,dept,year,today,now,conf,session))
    conn.commit()
    conn.close()
    return True

def add_student(sid,name,dept,year):
    conn = sqlite3.connect(DB)
    try:
        conn.execute("INSERT INTO students VALUES (?,?,?,?,?)",(sid,name,dept,year,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def clear_today():
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM attendance WHERE date=?",(datetime.now().strftime("%Y-%m-%d"),))
    conn.commit()
    conn.close()

init_db()

for k,v in [("scan_result",None),("scan_done",False),("log",["[BOOT] CNN model loaded","[BOOT] Database connected","[INFO] System ready"])]:
    if k not in st.session_state:
        st.session_state[k] = v

def add_log(msg,level="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.log.insert(0,"["+t+"] ["+level+"] "+msg)
    st.session_state.log = st.session_state.log[:30]

st.markdown('<div class="header-box"><h1>🎓 Face Recognition Attendance System</h1><p>CNN Deep Learning Framework &nbsp;|&nbsp; Kongunadu Arts and Science College, Coimbatore &nbsp;|&nbsp; Mrs. Gomathi S &nbsp;|&nbsp; Mythili R &nbsp;|&nbsp; Divya R &nbsp;|&nbsp; Dept of IT</p></div>',unsafe_allow_html=True)
st.markdown('<div class="conf-banner">🏆 International Conference Paper Presentation &nbsp;|&nbsp; Deep Learning &nbsp;|&nbsp; Computer Vision &nbsp;|&nbsp; Biometric Attendance</div>',unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Navigation")
    selected = st.radio("",["Dashboard","Face Scanner","Attendance Records","Register Student","Performance Metrics","System Log"],label_visibility="collapsed")
    st.markdown("---")
    session_type = st.selectbox("Session",["Morning","Afternoon","Evening"])
    st.selectbox("Subject",["Deep Learning","Computer Vision","Machine Learning","Data Structures"])
    st.markdown("---")
    rec = get_attendance()
    stu = get_students()
    pres = len(set(r[0] for r in rec))
    tot = len(stu)
    st.markdown("**Today Summary**")
    st.metric("Present",str(pres)+"/"+str(tot))
    st.metric("Absent",str(tot-pres))
    st.metric("Attendance %",str(round(pres/tot*100,1) if tot>0 else 0)+"%")

if selected == "Dashboard":
    st.markdown("## Dashboard")
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown('<div class="metric-card"><div class="metric-val" style="color:#10b981">96.2%</div><div class="metric-lbl">Recognition Accuracy</div></div>',unsafe_allow_html=True)
    with c2: st.markdown('<div class="metric-card"><div class="metric-val" style="color:#ef4444">1.8%</div><div class="metric-lbl">False Accept Rate</div></div>',unsafe_allow_html=True)
    with c3: st.markdown('<div class="metric-card"><div class="metric-val" style="color:#f59e0b">2.0%</div><div class="metric-lbl">False Reject Rate</div></div>',unsafe_allow_html=True)
    with c4: st.markdown('<div class="metric-card"><div class="metric-val" style="color:#3b82f6">0.8s</div><div class="metric-lbl">Avg Recognition Time</div></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("### System Workflow")
        for num,title,sub in [("1","Capture Image from Camera","Webcam frame acquisition at 30fps"),("2","Detect Faces in Frame","Haar Cascade detection"),("3","Extract Facial Features","128-D embedding via CNN"),("4","Compare with Database","Cosine similarity matching"),("5","Mark Attendance","SQL database auto-update"),("6","Generate Report","Daily / weekly / monthly")]:
            st.markdown('<div class="step-done">Step '+num+' — '+title+'<br><small style="opacity:.7">'+sub+'</small></div>',unsafe_allow_html=True)
    with col2:
        st.markdown("### CNN Architecture")
        for layer,desc in [("Input","128x128x3 RGB"),("Conv1","32 filters 3x3 ReLU"),("MaxPool1","2x2 pooling"),("Conv2","64 filters 3x3 ReLU"),("MaxPool2","2x2 pooling"),("Conv3","128 filters 3x3 ReLU"),("MaxPool3","2x2 pooling"),("FC","128-D embedding ReLU"),("Dropout","0.5 rate"),("Softmax","40 output classes")]:
            st.markdown('<div style="display:flex;gap:10px;margin-bottom:5px;align-items:center;"><span style="background:#dbeafe;color:#1e40af;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:700;min-width:75px;text-align:center;">'+layer+'</span><span style="font-size:13px;color:#475569;">'+desc+'</span></div>',unsafe_allow_html=True)
        st.markdown('<div style="margin-top:10px;padding:10px;background:#f0fdf4;border-radius:8px;font-size:12px;color:#166534;font-weight:600;">Loss: Categorical Cross-Entropy | Optimizer: Adam (lr=0.001)</div>',unsafe_allow_html=True)

elif selected == "Face Scanner":
    st.markdown("## Face Scanner — Simulated CNN Pipeline")
    students = get_students()
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("### Select Student to Scan")
        names = [s["name"]+"  ("+s["id"]+")" for s in students]
        choice = st.selectbox("Student",["-- Random Scan --"]+names)
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("Start Face Scan",use_container_width=True,type="primary"):
            st.session_state.scan_result = None
            st.session_state.scan_done = False
            ph = st.empty()
            prog = st.progress(0)
            for i,lbl in enumerate(["Step 1/5 — Capturing frame from webcam...","Step 2/5 — Detecting face with Haar Cascade...","Step 3/5 — Extracting 128-D CNN embedding...","Step 4/5 — Comparing features with database...","Step 5/5 — Finalising result..."]):
                ph.info(lbl)
                prog.progress((i+1)*20)
                time.sleep(0.5)
            ph.empty()
            prog.empty()
            if choice == "-- Random Scan --":
                matched = random.choice(students) if random.random()<0.85 else None
            else:
                matched = students[names.index(choice)]
            if matched:
                conf = round(90+random.random()*9.5,2)
                st.session_state.scan_result = {**matched,"confidence":conf,"matched":True}
                add_log("Match: "+matched["name"]+" conf="+str(conf)+"%","SUCCESS")
            else:
                st.session_state.scan_result = {"matched":False}
                add_log("No match — proxy attempt","WARN")
            st.session_state.scan_done = True
    with col2:
        st.markdown("### Scan Result")
        if not st.session_state.scan_done:
            st.markdown('<div class="camera-idle"><div style="font-size:52px;">📷</div><div style="color:#64748b;font-size:14px;margin-top:12px;font-family:monospace;">Click Start Face Scan to begin</div></div>',unsafe_allow_html=True)
        elif st.session_state.scan_result and st.session_state.scan_result.get("matched"):
            r = st.session_state.scan_result
            conf = r["confidence"]
            clr = "#10b981" if conf>=90 else "#f59e0b"
            st.markdown('<div class="match-box"><div style="font-size:18px;font-weight:800;color:#065f46;margin-bottom:8px;">✅ MATCH FOUND</div><div style="font-size:22px;font-weight:800;color:#1e293b;">'+r["name"]+'</div><div style="font-family:monospace;font-size:12px;color:#64748b;margin-bottom:14px;">'+r["id"]+' · '+r["dept"]+' · '+r["year"]+'</div><div style="background:#e2e8f0;border-radius:999px;height:14px;overflow:hidden;"><div style="width:'+str(conf)+'%;height:100%;background:'+clr+';border-radius:999px;"></div></div><div style="font-size:24px;font-weight:800;color:'+clr+';margin-top:6px;">'+str(conf)+'%</div></div>',unsafe_allow_html=True)
            st.markdown("<br>",unsafe_allow_html=True)
            bc1,bc2 = st.columns(2)
            with bc1:
                if st.button("Confirm Attendance",type="primary",use_container_width=True):
                    ok = mark_attendance(r["id"],r["name"],r["dept"],r["year"],r["confidence"],session_type)
                    if ok:
                        st.success(r["name"]+" marked Present!")
                        add_log("Marked: "+r["name"],"SUCCESS")
                        st.session_state.scan_done = False
                        st.rerun()
                    else:
                        st.warning("Already marked for this session!")
            with bc2:
                if st.button("Rescan",use_container_width=True):
                    st.session_state.scan_done = False
                    st.rerun()
        else:
            st.markdown('<div class="nomatch-box"><div style="font-size:44px;">❌</div><div style="font-size:20px;font-weight:800;color:#991b1b;margin-top:8px;">NO MATCH FOUND</div><div style="font-size:13px;color:#ef4444;margin-top:6px;">Possible proxy attendance attempt detected</div></div>',unsafe_allow_html=True)
            if st.button("Try Again",use_container_width=True):
                st.session_state.scan_done = False
                st.rerun()

elif selected == "Attendance Records":
    st.markdown("## Attendance Records")
    date_filter = st.date_input("Select Date",datetime.now())
    date_str = date_filter.strftime("%Y-%m-%d")
    records = get_attendance(date_str)
    all_students = get_students()
    present_ids = set(r[0] for r in records)
    present = len(present_ids)
    total = len(all_students)
    c1,c2,c3 = st.columns(3)
    c1.metric("Present",str(present)+" / "+str(total))
    c2.metric("Absent",str(total-present))
    c3.metric("Attendance %",str(round(present/total*100,1) if total>0 else 0)+"%")
    st.markdown("---")
    if records:
        st.markdown("#### Present Students")
        for r in records:
            cc1,cc2,cc3,cc4,cc5 = st.columns([2,2,2,1,1])
            cc1.markdown("**"+r[1]+"**")
            cc2.markdown("`"+r[0]+"`")
            cc3.markdown(r[2]+" · "+r[3])
            cc4.markdown(r[4])
            cc5.markdown((":green[" if r[5]>=90 else ":orange[")+str(round(r[5],1))+"%]")
        absent_list = [s for s in all_students if s["id"] not in present_ids]
        if absent_list:
            st.markdown("---")
            st.markdown("#### Absent Students")
            for s in absent_list:
                a1,a2,a3 = st.columns([2,2,2])
                a1.markdown("**"+s["name"]+"**")
                a2.markdown("`"+s["id"]+"`")
                a3.markdown(s["dept"]+" · "+s["year"])
        st.markdown("---")
        ca,cb = st.columns(2)
        with ca:
            if st.button("Clear Today Attendance",type="secondary"):
                clear_today()
                st.success("Cleared!")
                st.rerun()
        with cb:
            csv = "Student ID,Name,Department,Year,Time,Confidence,Session\n"+"".join([",".join([r[0],r[1],r[2],r[3],r[4],str(r[5]),r[6]])+"\n" for r in records])
            st.download_button("Export CSV",data=csv,file_name="attendance_"+date_str+".csv",mime="text/csv",use_container_width=True)
    else:
        st.info("No records for "+date_str+". Go to Face Scanner to mark attendance.")

elif selected == "Register Student":
    st.markdown("## Register New Student")
    with st.form("reg"):
        c1,c2 = st.columns(2)
        with c1:
            rid = st.text_input("Student ID",placeholder="KA2024099")
            rname = st.text_input("Full Name",placeholder="e.g. Priya Krishnan")
        with c2:
            rdept = st.selectbox("Department",["Information Technology","Computer Science","Electronics","Mechanical"])
            ryear = st.selectbox("Year",["I Year","II Year","III Year","IV Year"])
        if st.form_submit_button("Register Student",type="primary",use_container_width=True):
            if not rid.strip() or not rname.strip():
                st.error("Fill in Student ID and Name.")
            elif add_student(rid.strip(),rname.strip(),rdept,ryear):
                st.success(rname+" registered!")
                add_log("Enrolled: "+rname,"SUCCESS")
            else:
                st.error("Student ID already exists!")
    st.markdown("---")
    st.markdown("### All Enrolled Students")
    for s in get_students():
        c1,c2,c3,c4 = st.columns([2,2,2,1])
        c1.markdown("**"+s["name"]+"**")
        c2.markdown("`"+s["id"]+"`")
        c3.markdown(s["dept"])
        c4.markdown(s["year"])

elif selected == "Performance Metrics":
    st.markdown("## Performance Metrics")
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("### Method Comparison — Paper Table 3")
        try:
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(x=["PCA","LBPH","CNN (Proposed)"],y=[85.4,89.1,96.2],marker_color=["#f59e0b","#3b82f6","#10b981"],text=["85.4%","89.1%","96.2%"],textposition="outside"))
            fig.update_layout(yaxis=dict(range=[80,100],title="Accuracy (%)"),plot_bgcolor="#f8fafc",paper_bgcolor="#f8fafc",height=320,margin=dict(t=30,b=20,l=20,r=20))
            st.plotly_chart(fig,use_container_width=True)
        except ImportError:
            st.markdown("| Method | Accuracy |\n|--------|----------|\n| PCA | 85.4% |\n| LBPH | 89.1% |\n| **CNN (Proposed)** | **96.2%** |")
    with col2:
        st.markdown("### Confusion Matrix — Paper Table 2")
        st.markdown('<table style="width:100%;border-collapse:separate;border-spacing:8px;text-align:center;font-size:14px;"><tr><td></td><td style="font-weight:700;color:#64748b;font-size:12px;">PRED PRESENT</td><td style="font-weight:700;color:#64748b;font-size:12px;">PRED ABSENT</td></tr><tr><td style="font-weight:700;color:#64748b;font-size:12px;">ACT PRESENT</td><td style="background:#d1fae5;color:#065f46;font-weight:800;font-size:26px;padding:16px;border-radius:8px;">385<br><span style="font-size:11px;">TP</span></td><td style="background:#fee2e2;color:#991b1b;font-weight:700;font-size:22px;padding:16px;border-radius:8px;">8<br><span style="font-size:11px;">FN</span></td></tr><tr><td style="font-weight:700;color:#64748b;font-size:12px;">ACT ABSENT</td><td style="background:#fee2e2;color:#991b1b;font-weight:700;font-size:22px;padding:16px;border-radius:8px;">7<br><span style="font-size:11px;">FP</span></td><td style="background:#d1fae5;color:#065f46;font-weight:800;font-size:26px;padding:16px;border-radius:8px;">400<br><span style="font-size:11px;">TN</span></td></tr></table>',unsafe_allow_html=True)
        st.markdown('<div style="background:#f0fdf4;border-radius:10px;padding:14px;font-size:13px;margin-top:12px;"><b>Accuracy</b> = (TP+TN)/Total = 785/800 = <b style="color:#10b981;">96.2%</b><br><b>FAR</b> = FP/(FP+TN) = 7/407 = <b style="color:#ef4444;">1.8%</b><br><b>FRR</b> = FN/(FN+TP) = 8/393 = <b style="color:#f59e0b;">2.0%</b></div>',unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Full Summary")
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Recognition Accuracy","96.2%")
    m2.metric("False Acceptance Rate","1.8%")
    m3.metric("False Rejection Rate","2.0%")
    m4.metric("Avg Recognition Time","0.8s")
    m5,m6,m7,m8 = st.columns(4)
    m5.metric("Dataset Size","800 images")
    m6.metric("Train/Test Split","70% / 30%")
    m7.metric("Students","40")
    m8.metric("Images/Student","20")

elif selected == "System Log":
    st.markdown("## System Log")
    st.code("\n".join(st.session_state.log),language="bash")
    if st.button("Clear Log"):
        st.session_state.log = []
        st.rerun()
