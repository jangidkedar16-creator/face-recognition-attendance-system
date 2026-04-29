from flask import Flask, render_template, request, redirect, session, Response, send_file
import cv2, sqlite3, pickle, datetime, face_recognition, os, pandas as pd

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB ----------------


def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT, roll TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, time TEXT, date TEXT)""")
    
    conn.commit()
    conn.close()   
    
    
init_db()   

# ---------------- LOAD ENCODINGS ----------------
if os.path.exists("encodings.pkl"):
    with open("encodings.pkl","rb") as f:
        data = pickle.load(f)
else:
    data = {"encodings": [], "names": []}

# ---------------- LOGIN ----------------
@app.route('/',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "admin123":
            session['user'] = "admin"
            return redirect('/dashboard')
    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    conn=sqlite3.connect('database.db')
    c=conn.cursor()

    total=c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    present=c.execute("SELECT COUNT(DISTINCT name) FROM attendance WHERE date=date('now')").fetchone()[0]

    percent=(present/total*100) if total>0 else 0

    recent = c.execute("""
    SELECT name, time FROM attendance 
    WHERE date=date('now') 
    ORDER BY time DESC LIMIT 5
    """).fetchall()

    return render_template("dashboard.html",
        total=total,
        present=present,
        percent=round(percent,2),
        recent=recent
    )

# ---------------- MARK ATTENDANCE ----------------
def mark(name):
    conn=sqlite3.connect('database.db')
    c=conn.cursor()

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    already = c.execute(
        "SELECT * FROM attendance WHERE name=? AND date=? AND roll=?",
        (name, today)
    ).fetchone()

    if not already:
        c.execute(
            "INSERT INTO attendance(name,time,date) VALUES (?,?,?)",
            (name, datetime.datetime.now().strftime("%H:%M:%S"), today)
        )
        conn.commit()

    conn.close()

# ---------------- CAMERA ----------------
def gen():
    cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)

    try:
        while True:
            ret,frame=cap.read()
            if not ret:
                break

            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            faces=face_recognition.face_locations(rgb)
            encs=face_recognition.face_encodings(rgb,faces)

            for enc,face in zip(encs,faces):
                matches=face_recognition.compare_faces(data["encodings"],enc)
                name="Unknown"

                if True in matches:
                    i=matches.index(True)
                    name=data["names"][i]
                    mark(name)

                t,r,b,l=face
                cv2.rectangle(frame,(l,t),(r,b),(0,255,0),2)
                cv2.putText(frame,name,(l,t-10),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,255,0),2)

            _,buffer=cv2.imencode('.jpg',frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'+buffer.tobytes()+b'\r\n')

    finally:
        cap.release()

@app.route('/video')
def video():
    return Response(gen(),mimetype='multipart/x-mixed-replace; boundary=frame')

#  to capture real time image
@app.route('/capture')
def capture():
    cap = cv2.VideoCapture(1)

    ret, frame = cap.read()
    if not ret:
        return "Camera Error"

    filename = f"capture_{datetime.datetime.now().strftime('%H%M%S')}.jpg"

    if not os.path.exists("captures"):
        os.makedirs("captures")

    path = os.path.join("captures", filename)
    cv2.imwrite(path, frame)

    cap.release()

    return f"Image Saved: {filename}"

# ---------------- REGISTER ----------------
@app.route('/register',methods=['GET','POST'])
def register():
    global data

    if request.method=='POST':
        name=request.form['name']
        image=request.files['image']
        roll = request.form['roll']
        
        if not os.path.exists("known_faces"):
            os.makedirs("known_faces")

        path=f"known_faces/{name}.jpg"
        image.save(path)
        
        img = face_recognition.load_image_file(path)
        enc = face_recognition.face_encodings(img)

        if len(enc) > 0:
            data["encodings"].append(enc[0])
            data["names"].append(name)

            with open("encodings.pkl","wb") as f:
                pickle.dump(data,f)

        conn=sqlite3.connect('database.db')
        conn.execute("INSERT INTO students(name, roll) VALUES (?, ?)",(name, roll))
        conn.commit()
        conn.close()

        return redirect('/students')

    return render_template("register.html")

# ---------------- STUDENTS ----------------
@app.route('/students')
def students():
    conn=sqlite3.connect('database.db')
    data2=conn.execute("SELECT * FROM students").fetchall()
    return render_template("students.html",data=data2)

# ---------------- RECORDS ----------------
@app.route('/records')
def records():
    conn=sqlite3.connect('database.db')
    data2=conn.execute("SELECT * FROM attendance").fetchall()
    return render_template("records.html",data=data2)

# ---------------- EXPORT csv----------------
@app.route('/export')
def export_attendance():
    import sqlite3
    import pandas as pd
    import os
    from flask import send_file

    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query("SELECT * FROM attendance", conn)
    conn.close()

    file_name = os.path.join(os.getcwd(), "attendance.xlsx")

    # file create karo
    df.to_excel(file_name, index=False)

    # file bhejo
    return send_file(file_name, as_attachment=True)

#----------------DELETE-------------
@app.route('/delete_student/<int:id>')
def delete_student(id):
    conn = sqlite3.connect('database.db')
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/students')


#----------------EDIT-----------------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']

        c.execute("UPDATE students SET name=?, roll=? WHERE id=?", (name, roll, id))
        conn.commit()
        conn.close()

        return redirect('/students')

    # GET request → data fetch
    c.execute("SELECT * FROM students WHERE id=?", (id,))
    student = c.fetchone()
    conn.close()

    return render_template('edit_student.html', student=student)
#----------------logout----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
#
# ---------------- RUN ----------------

#-------- run--------#
if __name__ == "__main__":
    app.run(debug=True)