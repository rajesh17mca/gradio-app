import gradio as gr
import sqlite3
import re
import json
import uuid
import time

# ---------- DATABASE SETUP ----------
conn = sqlite3.connect('students.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS students (
    roll_no TEXT PRIMARY KEY,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    course TEXT,
    cgpa REAL,
    grade TEXT
)
''')
conn.commit()

# ---------- LOGGING SYSTEM ----------
LOG_FILE = "logs/app_logs.log"

def log_action(action, start_time, headers=None):
    end_time = time.time()
    log_entry = {
        "transaction_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "action": action,
        "time_taken_ms": int((end_time - start_time) * 1000),
        "headers": headers or {}
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# ---------- HELPER FUNCTIONS ----------
def generate_roll_no(course):
    year = 2025
    c.execute("SELECT COUNT(*) FROM students WHERE course=?", (course,))
    count = c.fetchone()[0] + 1
    return f"{year}R1{course.upper()}{count}"

def add_student(first, middle, last, phone, email, address, course, cgpa):
    roll_no = generate_roll_no(course)
    c.execute('''
        INSERT INTO students
        (roll_no, first_name, middle_name, last_name, phone, email, address, course, cgpa)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (roll_no, first, middle, last, phone, email, address, course, cgpa))
    conn.commit()
    start_time = time.time()
    log_action(f"Registered student {roll_no}", start_time)
    return f"Student added with Roll No: {roll_no}"

def list_students():
    c.execute("SELECT * FROM students ORDER BY roll_no")
    rows = c.fetchall()
    return rows

def get_student_options():
    c.execute("SELECT roll_no FROM students")
    return [r[0] for r in c.fetchall()]

def load_student(roll_no):
    c.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,))
    student = c.fetchone()
    if not student:
        return [""]*10
    return student[1:]  # return all fields except roll_no

def update_student_gr(first, middle, last, phone, email, address, course, cgpa, grade, roll_no):
    start_time = time.time()
    if not re.fullmatch(r'\d{10}', phone):
        return "Invalid phone number"
    elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
        return "Invalid email address"
    c.execute('''
        UPDATE students 
        SET first_name=?, middle_name=?, last_name=?, phone=?, email=?, address=?, course=?, cgpa=?, grade=? 
        WHERE roll_no=?
    ''', (first, middle, last, phone, email, address, course, cgpa, grade, roll_no))
    conn.commit()
    log_action(f"Updated student {roll_no}", start_time)
    return f"Student {roll_no} updated successfully!"

# ---------- GRADIO INTERFACES ----------

# Register Interface
def register_interface(first, middle, last, phone, email, address, course, cgpa):
    if not re.fullmatch(r'\d{10}', phone):
        return "Invalid phone number"
    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
        return "Invalid email"
    return add_student(first, middle, last, phone, email, address, course, cgpa)

register_inputs = [
    gr.Textbox(label="First Name"),
    gr.Textbox(label="Middle Name"),
    gr.Textbox(label="Last Name"),
    gr.Textbox(label="Phone Number"),
    gr.Textbox(label="Email"),
    gr.Textbox(label="Address"),
    gr.Dropdown(["MCA", "MBA", "MTECH", "BTECH"], label="Course"),
    gr.Number(label="CGPA", value=0.0)
]

register_output = gr.Textbox(label="Result")

register_demo = gr.Interface(
    fn=register_interface,
    inputs=register_inputs,
    outputs=register_output,
    title="Register Student"
)

# List Students Interface
def list_interface():
    rows = list_students()
    headers = ["Roll No","First","Middle","Last","Phone","Email","Address","Course","CGPA","Grade"]
    table = [headers] + [list(r) for r in rows]
    return table

list_demo = gr.Interface(
    fn=list_interface,
    inputs=[],
    outputs=gr.Dataframe(headers=None),
    title="List Students"
)

# Update Interface
def load_student_for_update(roll_no):
    fields = load_student(roll_no)
    return fields

update_inputs = [
    gr.Textbox(label="Roll Number"),
]

update_outputs = [
    gr.Textbox(label="First Name"),
    gr.Textbox(label="Middle Name"),
    gr.Textbox(label="Last Name"),
    gr.Textbox(label="Phone Number"),
    gr.Textbox(label="Email"),
    gr.Textbox(label="Address"),
    gr.Dropdown(["MCA", "MBA", "MTECH", "BTECH"], label="Course"),
    gr.Number(label="CGPA", value=0.0),
    gr.Textbox(label="Grade")
]

def update_student_interface(first, middle, last, phone, email, address, course, cgpa, grade, roll_no):
    return update_student_gr(first, middle, last, phone, email, address, course, cgpa, grade, roll_no)

update_demo = gr.Interface(
    fn=update_student_interface,
    inputs=[
        gr.Textbox(label="First Name"),
        gr.Textbox(label="Middle Name"),
        gr.Textbox(label="Last Name"),
        gr.Textbox(label="Phone Number"),
        gr.Textbox(label="Email"),
        gr.Textbox(label="Address"),
        gr.Dropdown(["MCA", "MBA", "MTECH", "BTECH"], label="Course"),
        gr.Number(label="CGPA", value=0.0),
        gr.Textbox(label="Grade"),
        gr.Textbox(label="Roll Number")
    ],
    outputs=gr.Textbox(label="Result"),
    title="Update Student"
)

# ---------- GRADIO TAB LAYOUT ----------
app = gr.TabbedInterface(
    [register_demo, list_demo, update_demo],
    ["Register Student", "List Students", "Update Student"]
)

app.launch()
