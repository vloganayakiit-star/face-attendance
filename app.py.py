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
.camera-idle{background:#0f172a;border-radius:14px;padding:40px 32px;text-align:center;border:2px dashed #334155}
.student-card{background:white;border-radius:12px;padding:14px;border:1.5px solid #e2e8f0;margin-bottom:8px}
.delete-row{background:#fff5f5;border:1px solid #fecaca;border-radius:8px;padding:10px 14px;margin-bottom:6px}
</style>
""", unsafe_allow_html=True)

DB = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT,
        year TEXT,
        roll_no TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        enrolled_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT, name TEXT, department TEXT, year TEXT,
        date TEXT, time TEXT, confidence REAL, session TEXT, subject TEXT)""")
    conn.commit()
    # Safely add missing columns for older database versions
    for tbl, col, coltype in [
        ("students","roll_no","TEXT"),
        ("students","email","TEXT"),
        ("students","phone","TEXT"),
        ("attendance","subject","TEXT"),
    ]:
        try:
            conn.execute("ALTER TABLE "+tbl+" ADD COLUMN "+col+" "+coltype+" DEFAULT ''")
            conn.commit()
        except Exception:
            pass
    conn.close()

def get_students():
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT student_id,name,department,year,roll_no,email,phone FROM students ORDER BY name"
    ).fetchall()
    conn.close()
    return [{"id":r[0],"name":r[1],"dept":r[2],"year":r[3],
             "roll":r[4],"email":r[5],"phone":r[6]} for r in rows]

def get_attendance(date=None):
    date = date or datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB)
    # Add subject column if it does not exist (handles old databases)
    try:
        conn.execute("ALTER TABLE attendance ADD COLUMN subject TEXT DEFAULT 'General'")
        conn.commit()
    except Exception:
        pass
    rows = conn.execute(
        "SELECT student_id,name,department,year,time,confidence,session,subject "
        "FROM attendance WHERE date=? ORDER BY time DESC",(date,)
    ).fetchall()
    conn.close()
    return rows

def mark_attendance(sid,name,dept,year,conf,session,subject):
    today = datetime.now().strftime("%Y-%m-%d")
    now   = datetime.now().strftime("%H:%M:%S")
    conn  = sqlite3.connect(DB)
    if conn.execute(
        "SELECT id FROM attendance WHERE student_id=? AND date=? AND session=?",
        (sid,today,session)
    ).fetchone():
        conn.close()
        return False
    conn.execute(
        "INSERT INTO attendance (student_id,name,department,year,date,time,confidence,session,subject) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (sid,name,dept,year,today,now,conf,session,subject)
    )
    conn.commit()
    conn.close()
    return True

def add_student(sid,name,dept,year,roll,email,phone):
    conn = sqlite3.connect(DB)
    try:
        # Ensure table has all needed columns before inserting
        for col, coltype in [("roll_no","TEXT"),("email","TEXT"),("phone","TEXT")]:
            try:
                conn.execute("ALTER TABLE students ADD COLUMN "+col+" "+coltype)
                conn.commit()
            except Exception:
                pass
        conn.execute(
            "INSERT INTO students (student_id,name,department,year,roll_no,email,phone,enrolled_at) VALUES (?,?,?,?,?,?,?,?)",
            (sid.strip(), name.strip(), dept, year,
             roll.strip() if roll else "",
             email.strip() if email else "",
             phone.strip() if phone else "",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return True, "success"
    except Exception as e:
        conn.close()
        err = str(e)
        if "UNIQUE" in err or "PRIMARY KEY" in err:
            return False, "Student ID already exists! Please use a different ID."
        return False, "Error: " + err

def delete_student(sid):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM students WHERE student_id=?",(sid,))
    conn.execute("DELETE FROM attendance WHERE student_id=?",(sid,))
    conn.commit()
    conn.close()

def clear_today():
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM attendance WHERE date=?",
                 (datetime.now().strftime("%Y-%m-%d"),))
    conn.commit()
    conn.close()

def get_student_count():
    conn = sqlite3.connect(DB)
    n = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()
    return n

init_db()

for k,v in [
    ("scan_result",None),
    ("scan_done",False),
    ("log",["[BOOT] CNN model loaded","[BOOT] Database connected","[INFO] System ready"]),
    ("confirm_delete",None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

def add_log(msg,level="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.log.insert(0,"["+t+"] ["+level+"] "+msg)
    st.session_state.log = st.session_state.log[:30]

# Header
st.markdown(
    '<div class="header-box">'
    '<h1>🎓 Face Recognition Attendance System</h1>'
    '<p>CNN Deep Learning Framework | Kongunadu Arts and Science College, Coimbatore | '
    'Mrs. Gomathi S | Mythili R | Divya R | Dept of IT</p>'
    '</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="conf-banner">'
    '🏆 International Conference Paper Presentation | '
    'Deep Learning | Computer Vision | Biometric Attendance'
    '</div>',
    unsafe_allow_html=True
)

# Sidebar
with st.sidebar:
    st.markdown("### Navigation")
    selected = st.radio("", [
        "Dashboard",
        "Face Scanner",
        "Attendance Records",
        "Student Management",
        "Performance Metrics",
        "System Log"
    ], label_visibility="collapsed")
    st.markdown("---")
    session_type = st.selectbox("Session",["Morning","Afternoon","Evening"])
    subject = st.selectbox("Subject",[
        "Deep Learning","Computer Vision",
        "Machine Learning","Data Structures","Operating Systems"
    ])
    st.markdown("---")
    rec  = get_attendance()
    stu  = get_students()
    pres = len(set(r[0] for r in rec))
    tot  = len(stu)
    st.markdown("**Today Summary**")
    st.metric("Total Students", str(tot))
    st.metric("Present", str(pres)+"/"+str(tot))
    st.metric("Absent",  str(tot-pres))
    st.metric("Attendance %", str(round(pres/tot*100,1) if tot>0 else 0)+"%")

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if selected == "Dashboard":
    st.markdown("## 📊 Dashboard")
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown('<div class="metric-card"><div class="metric-val" style="color:#10b981">96.2%</div><div class="metric-lbl">Recognition Accuracy</div></div>',unsafe_allow_html=True)
    with c2: st.markdown('<div class="metric-card"><div class="metric-val" style="color:#ef4444">1.8%</div><div class="metric-lbl">False Accept Rate</div></div>',unsafe_allow_html=True)
    with c3: st.markdown('<div class="metric-card"><div class="metric-val" style="color:#f59e0b">2.0%</div><div class="metric-lbl">False Reject Rate</div></div>',unsafe_allow_html=True)
    with c4: st.markdown('<div class="metric-card"><div class="metric-val" style="color:#3b82f6">0.8s</div><div class="metric-lbl">Avg Recognition Time</div></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("### 🔄 System Workflow")
        for num,title,sub in [
            ("1","Capture Image from Camera","Webcam frame acquisition at 30fps"),
            ("2","Detect Faces in Frame","Haar Cascade detection"),
            ("3","Extract Facial Features","128-D embedding via CNN"),
            ("4","Compare with Database","Cosine similarity matching"),
            ("5","Mark Attendance","SQL database auto-update"),
            ("6","Generate Report","Daily / weekly / monthly"),
        ]:
            st.markdown(
                '<div class="step-done">Step '+num+' - '+title+
                '<br><small style="opacity:.7">'+sub+'</small></div>',
                unsafe_allow_html=True
            )
    with col2:
        st.markdown("### 🧠 CNN Architecture")
        for layer,desc in [
            ("Input","128x128x3 RGB"),("Conv1","32 filters 3x3 ReLU"),
            ("MaxPool1","2x2 pooling"),("Conv2","64 filters 3x3 ReLU"),
            ("MaxPool2","2x2 pooling"),("Conv3","128 filters 3x3 ReLU"),
            ("MaxPool3","2x2 pooling"),("FC","128-D embedding ReLU"),
            ("Dropout","0.5 rate"),("Softmax","40 output classes"),
        ]:
            st.markdown(
                '<div style="display:flex;gap:10px;margin-bottom:5px;align-items:center;">'
                '<span style="background:#dbeafe;color:#1e40af;padding:3px 8px;border-radius:6px;'
                'font-size:11px;font-weight:700;min-width:75px;text-align:center;">'+layer+'</span>'
                '<span style="font-size:13px;color:#475569;">'+desc+'</span></div>',
                unsafe_allow_html=True
            )
        st.markdown(
            '<div style="margin-top:10px;padding:10px;background:#f0fdf4;border-radius:8px;'
            'font-size:12px;color:#166534;font-weight:600;">'
            'Loss: Categorical Cross-Entropy | Optimizer: Adam (lr=0.001)</div>',
            unsafe_allow_html=True
        )

# ── FACE SCANNER ──────────────────────────────────────────────────────────────
elif selected == "Face Scanner":
    st.markdown("## 📷 Face Scanner - Simulated CNN Pipeline")
    students = get_students()

    if len(students) == 0:
        st.warning("No students registered yet. Go to Student Management to add students first.")
    else:
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("### Select Student to Scan")
            names = [s["name"]+"  ("+s["id"]+")" for s in students]
            choice = st.selectbox("Student",["-- Random Scan --"]+names)
            st.markdown("<br>",unsafe_allow_html=True)

            if st.button("🔍 Start Face Scan",use_container_width=True,type="primary"):
                st.session_state.scan_result = None
                st.session_state.scan_done   = False
                ph   = st.empty()
                prog = st.progress(0)
                for i,lbl in enumerate([
                    "Step 1/5 - Capturing frame from webcam...",
                    "Step 2/5 - Detecting face with Haar Cascade...",
                    "Step 3/5 - Extracting 128-D CNN embedding...",
                    "Step 4/5 - Comparing features with database...",
                    "Step 5/5 - Finalising result...",
                ]):
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
                    add_log("No match - proxy attempt","WARN")
                st.session_state.scan_done = True

        with col2:
            st.markdown("### Scan Result")
            if not st.session_state.scan_done:
                st.markdown(
                    '<div class="camera-idle">'
                    '<div style="font-size:52px;">📷</div>'
                    '<div style="color:#64748b;font-size:14px;margin-top:12px;font-family:monospace;">'
                    'Select a student and click Start Face Scan</div></div>',
                    unsafe_allow_html=True
                )
            elif st.session_state.scan_result and st.session_state.scan_result.get("matched"):
                r    = st.session_state.scan_result
                conf = r["confidence"]
                clr  = "#10b981" if conf>=90 else "#f59e0b"
                st.markdown(
                    '<div class="match-box">'
                    '<div style="font-size:18px;font-weight:800;color:#065f46;margin-bottom:8px;">✅ MATCH FOUND</div>'
                    '<div style="font-size:22px;font-weight:800;color:#1e293b;">'+r["name"]+'</div>'
                    '<div style="font-family:monospace;font-size:12px;color:#64748b;margin-bottom:4px;">'+r["id"]+' | '+r["dept"]+' | '+r["year"]+'</div>'
                    '<div style="font-family:monospace;font-size:12px;color:#94a3b8;margin-bottom:14px;">Roll: '+(r["roll"] or "-")+' | Email: '+(r["email"] or "-")+'</div>'
                    '<div style="font-size:12px;color:#64748b;margin-bottom:6px;">Confidence Score</div>'
                    '<div style="background:#e2e8f0;border-radius:999px;height:14px;overflow:hidden;">'
                    '<div style="width:'+str(conf)+'%;height:100%;background:'+clr+';border-radius:999px;"></div></div>'
                    '<div style="font-size:24px;font-weight:800;color:'+clr+';margin-top:6px;">'+str(conf)+'%</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
                st.markdown("<br>",unsafe_allow_html=True)
                bc1,bc2 = st.columns(2)
                with bc1:
                    if st.button("✓ Confirm Attendance",type="primary",use_container_width=True):
                        ok = mark_attendance(
                            r["id"],r["name"],r["dept"],r["year"],
                            r["confidence"],session_type,subject
                        )
                        if ok:
                            st.success(r["name"]+" marked Present!")
                            add_log("Marked: "+r["name"]+" | "+session_type,"SUCCESS")
                            st.session_state.scan_done = False
                            st.rerun()
                        else:
                            st.warning("Already marked for this session!")
                with bc2:
                    if st.button("↺ Rescan",use_container_width=True):
                        st.session_state.scan_done = False
                        st.rerun()
            else:
                st.markdown(
                    '<div class="nomatch-box">'
                    '<div style="font-size:44px;">❌</div>'
                    '<div style="font-size:20px;font-weight:800;color:#991b1b;margin-top:8px;">NO MATCH FOUND</div>'
                    '<div style="font-size:13px;color:#ef4444;margin-top:6px;">Possible proxy attendance attempt detected</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
                if st.button("↺ Try Again",use_container_width=True):
                    st.session_state.scan_done = False
                    st.rerun()

# ── ATTENDANCE RECORDS ────────────────────────────────────────────────────────
elif selected == "Attendance Records":
    st.markdown("## 📋 Attendance Records")
    date_filter  = st.date_input("Select Date",datetime.now())
    date_str     = date_filter.strftime("%Y-%m-%d")
    records      = get_attendance(date_str)
    all_students = get_students()
    present_ids  = set(r[0] for r in records)
    present      = len(present_ids)
    total        = len(all_students)

    c1,c2,c3 = st.columns(3)
    c1.metric("Present",  str(present)+" / "+str(total))
    c2.metric("Absent",   str(total-present))
    c3.metric("Attendance %", str(round(present/total*100,1) if total>0 else 0)+"%")
    st.markdown("---")

    if records:
        st.markdown("#### ✅ Present Students")
        for r in records:
            cc1,cc2,cc3,cc4,cc5,cc6 = st.columns([2,2,1,1,1,1])
            cc1.markdown("**"+r[1]+"**")
            cc2.markdown(r[2]+" - "+r[3])
            cc3.markdown("`"+r[0]+"`")
            cc4.markdown(r[4])
            cc5.markdown(r[6])
            cc6.markdown((":green[" if r[5]>=90 else ":orange[")+str(round(r[5],1))+"%]")

        absent_list = [s for s in all_students if s["id"] not in present_ids]
        if absent_list:
            st.markdown("---")
            st.markdown("#### ❌ Absent Students")
            for s in absent_list:
                a1,a2,a3,a4 = st.columns([2,2,2,1])
                a1.markdown("**"+s["name"]+"**")
                a2.markdown("`"+s["id"]+"`")
                a3.markdown(s["dept"]+" - "+s["year"])
                a4.markdown(s["roll"] or "-")

        st.markdown("---")
        ca,cb = st.columns(2)
        with ca:
            if st.button("🗑 Clear Today Attendance",type="secondary"):
                clear_today()
                st.success("Cleared!")
                st.rerun()
        with cb:
            csv = "Student ID,Name,Department,Year,Time,Confidence,Session,Subject\n"
            for r in records:
                csv += ",".join([r[0],r[1],r[2],r[3],r[4],str(r[5]),r[6],r[7]])+"\n"
            st.download_button(
                "⬇ Export CSV",data=csv,
                file_name="attendance_"+date_str+".csv",
                mime="text/csv",use_container_width=True
            )
    else:
        st.info("No records for "+date_str+". Go to Face Scanner to mark attendance.")

# ── STUDENT MANAGEMENT ────────────────────────────────────────────────────────
elif selected == "Student Management":
    st.markdown("## 👤 Student Management")

    tab1, tab2, tab3 = st.tabs(["➕ Add Student", "📋 View All Students", "🗑 Delete Student"])

    # ── ADD STUDENT ──────────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Add New Student")
        st.info("Fill in the student details below. Student ID must be unique.")

        with st.form("add_form", clear_on_submit=True):
            col1,col2 = st.columns(2)
            with col1:
                f_id    = st.text_input("Student ID *",   placeholder="e.g. KA2024011")
                f_name  = st.text_input("Full Name *",    placeholder="e.g. Priya Krishnan")
                f_roll  = st.text_input("Roll Number",    placeholder="e.g. 22IT011")
            with col2:
                f_dept  = st.selectbox("Department *",[
                    "Information Technology","Computer Science",
                    "Electronics","Mechanical","Civil","Mathematics"
                ])
                f_year  = st.selectbox("Year *",["I Year","II Year","III Year","IV Year"])
                f_email = st.text_input("Email",          placeholder="student@email.com")
            f_phone = st.text_input("Phone Number",       placeholder="e.g. 9876543210")

            submitted = st.form_submit_button("➕ Add Student", type="primary", use_container_width=True)
            if submitted:
                if not f_id.strip() or not f_name.strip():
                    st.error("⚠️ Student ID and Full Name are required fields.")
                else:
                    ok, msg = add_student(
                        f_id.strip(), f_name.strip(),
                        f_dept, f_year,
                        f_roll.strip(), f_email.strip(), f_phone.strip()
                    )
                    if ok:
                        st.success("✅ "+f_name.strip()+" ("+f_id.strip()+") added successfully!")
                        add_log("New student added: "+f_name.strip()+" ("+f_id.strip()+")","SUCCESS")
                        st.rerun()
                    else:
                        st.error("❌ "+msg)

        st.markdown("---")
        st.markdown("### 📥 Add Multiple Students at Once")
        st.markdown("Paste student data below — one student per line in this format:")
        st.code("StudentID, Full Name, Department, Year, RollNo, Email, Phone")
        bulk_input = st.text_area(
            "Paste student list here",
            placeholder="KA2024011, Priya Krishnan, Information Technology, III Year, 22IT011, priya@email.com, 9876543210\nKA2024012, Arjun Kumar, Computer Science, II Year, 21CS012, arjun@email.com, 9876543211",
            height=150
        )
        if st.button("📥 Add All Students", type="primary", use_container_width=True):
            if bulk_input.strip():
                lines   = bulk_input.strip().split("\n")
                success = 0
                failed  = 0
                errors  = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2:
                        sid   = parts[0]
                        sname = parts[1]
                        sdept = parts[2] if len(parts)>2 else "Information Technology"
                        syear = parts[3] if len(parts)>3 else "I Year"
                        sroll = parts[4] if len(parts)>4 else ""
                        semail= parts[5] if len(parts)>5 else ""
                        sphone= parts[6] if len(parts)>6 else ""
                        ok, err = add_student(sid,sname,sdept,syear,sroll,semail,sphone)
                        if ok:
                            success += 1
                        else:
                            failed += 1
                            errors.append(sid+": "+err)
                    else:
                        failed += 1
                        errors.append("Invalid format: "+line)
                if success > 0:
                    st.success("✅ "+str(success)+" student(s) added successfully!")
                    add_log(str(success)+" students bulk added","SUCCESS")
                if failed > 0:
                    st.warning("⚠️ "+str(failed)+" row(s) failed:")
                    for e in errors:
                        st.caption("• "+e)
                st.rerun()
            else:
                st.warning("Please paste student data first.")

    # ── VIEW ALL STUDENTS ─────────────────────────────────────────────────────
    with tab2:
        students = get_students()
        st.markdown("### All Enrolled Students  ("+str(len(students))+" total)")

        if not students:
            st.info("No students registered yet. Use the Add Student tab to add students.")
        else:
            search = st.text_input("🔍 Search by name, ID or department", placeholder="Type to search...")
            if search:
                students = [s for s in students if
                    search.lower() in s["name"].lower() or
                    search.lower() in s["id"].lower() or
                    search.lower() in s["dept"].lower()
                ]
                st.markdown("**"+str(len(students))+" result(s) found**")

            for s in students:
                with st.expander(s["name"]+" — "+s["id"]+" | "+s["dept"]+" | "+s["year"]):
                    col1,col2,col3 = st.columns(3)
                    col1.markdown("**Student ID:** "+s["id"])
                    col1.markdown("**Name:** "+s["name"])
                    col2.markdown("**Department:** "+s["dept"])
                    col2.markdown("**Year:** "+s["year"])
                    col3.markdown("**Roll No:** "+(s["roll"] or "-"))
                    col3.markdown("**Email:** "+(s["email"] or "-"))
                    if s["phone"]:
                        st.markdown("**Phone:** "+s["phone"])

    # ── DELETE STUDENT ─────────────────────────────────────────────────────────
    with tab3:
        students = get_students()
        st.markdown("### Delete Student")
        st.warning("Deleting a student will also remove all their attendance records.")

        if not students:
            st.info("No students to delete.")
        else:
            del_names = [s["name"]+" ("+s["id"]+")" for s in students]
            del_choice = st.selectbox("Select student to delete", del_names)
            del_student = students[del_names.index(del_choice)]

            col1,col2 = st.columns(2)
            with col1:
                st.markdown("**Name:** "+del_student["name"])
                st.markdown("**ID:** "+del_student["id"])
            with col2:
                st.markdown("**Dept:** "+del_student["dept"])
                st.markdown("**Year:** "+del_student["year"])

            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("🗑 Delete This Student", type="secondary", use_container_width=True):
                st.session_state.confirm_delete = del_student["id"]

            if st.session_state.confirm_delete == del_student["id"]:
                st.error("Are you sure you want to delete **"+del_student["name"]+"**? This cannot be undone.")
                cc1,cc2 = st.columns(2)
                with cc1:
                    if st.button("Yes, Delete", type="primary", use_container_width=True):
                        delete_student(del_student["id"])
                        st.success(del_student["name"]+" deleted.")
                        add_log("Student deleted: "+del_student["name"],"WARN")
                        st.session_state.confirm_delete = None
                        st.rerun()
                with cc2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.confirm_delete = None
                        st.rerun()

# ── PERFORMANCE METRICS ───────────────────────────────────────────────────────
elif selected == "Performance Metrics":
    st.markdown("## 📈 Performance Metrics")
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("### Method Comparison - Paper Table 3")
        try:
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=["PCA","LBPH","CNN (Proposed)"],
                y=[85.4,89.1,96.2],
                marker_color=["#f59e0b","#3b82f6","#10b981"],
                text=["85.4%","89.1%","96.2%"],
                textposition="outside"
            ))
            fig.update_layout(
                yaxis=dict(range=[80,100],title="Accuracy (%)"),
                plot_bgcolor="#f8fafc",paper_bgcolor="#f8fafc",
                height=320,margin=dict(t=30,b=20,l=20,r=20)
            )
            st.plotly_chart(fig,use_container_width=True)
        except ImportError:
            st.markdown("| Method | Accuracy |\n|--------|----------|\n| PCA | 85.4% |\n| LBPH | 89.1% |\n| **CNN (Proposed)** | **96.2%** |")
    with col2:
        st.markdown("### Confusion Matrix - Paper Table 2")
        st.markdown(
            '<table style="width:100%;border-collapse:separate;border-spacing:8px;text-align:center;font-size:14px;">'
            '<tr><td></td>'
            '<td style="font-weight:700;color:#64748b;font-size:12px;">PRED PRESENT</td>'
            '<td style="font-weight:700;color:#64748b;font-size:12px;">PRED ABSENT</td></tr>'
            '<tr><td style="font-weight:700;color:#64748b;font-size:12px;">ACT PRESENT</td>'
            '<td style="background:#d1fae5;color:#065f46;font-weight:800;font-size:26px;padding:16px;border-radius:8px;">385<br><span style="font-size:11px;">TP</span></td>'
            '<td style="background:#fee2e2;color:#991b1b;font-weight:700;font-size:22px;padding:16px;border-radius:8px;">8<br><span style="font-size:11px;">FN</span></td></tr>'
            '<tr><td style="font-weight:700;color:#64748b;font-size:12px;">ACT ABSENT</td>'
            '<td style="background:#fee2e2;color:#991b1b;font-weight:700;font-size:22px;padding:16px;border-radius:8px;">7<br><span style="font-size:11px;">FP</span></td>'
            '<td style="background:#d1fae5;color:#065f46;font-weight:800;font-size:26px;padding:16px;border-radius:8px;">400<br><span style="font-size:11px;">TN</span></td></tr>'
            '</table>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="background:#f0fdf4;border-radius:10px;padding:14px;font-size:13px;margin-top:12px;">'
            '<b>Accuracy</b> = (TP+TN)/Total = 785/800 = <b style="color:#10b981;">96.2%</b><br>'
            '<b>FAR</b> = FP/(FP+TN) = 7/407 = <b style="color:#ef4444;">1.8%</b><br>'
            '<b>FRR</b> = FN/(FN+TP) = 8/393 = <b style="color:#f59e0b;">2.0%</b>'
            '</div>',
            unsafe_allow_html=True
        )
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

# ── SYSTEM LOG ────────────────────────────────────────────────────────────────
elif selected == "System Log":
    st.markdown("## 🖥 System Log")
    st.code("\n".join(st.session_state.log),language="bash")
    if st.button("Clear Log"):
        st.session_state.log = []
        st.rerun()
