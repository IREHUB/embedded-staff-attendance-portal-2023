import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import csv
import random


# ================= DATABASE SETUP =================
def init_db():
    conn = sqlite3.connect("school_management_pro.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        username TEXT UNIQUE,
        password TEXT,
        approved INTEGER DEFAULT 0)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER,
        timestamp TEXT,
        date TEXT,
        status TEXT,
        UNIQUE(staff_id, date))""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER,
        subject TEXT,
        day TEXT,
        slot_time TEXT,
        class_name TEXT,
        FOREIGN KEY(staff_id) REFERENCES staff(id))""")

    cursor.execute("SELECT * FROM admin WHERE id=1")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admin (username, password) VALUES ('admin', 'admin123')")
    conn.commit()
    return conn, cursor


conn, cursor = init_db()

# ================= CONFIGURATION =================
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
CLASSES = ["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"]
SCHOOL_SLOTS = ["08:00-08:40 (L1)", "08:40-09:20 (L2)", "09:20-10:00 (L3)",
                "10:15-10:55 (L4)", "10:55-11:35 (L5)", "11:35-12:15 (L6)",
                "12:45-01:25 (L7)", "01:25-02:05 (L8)", "02:30-03:00 (Ext)"]


# ================= UI HELPERS =================
def clear():
    for w in root.winfo_children(): w.destroy()


def card(title, bg_color="#e0e0e0"):
    wrapper = tk.Frame(root, bg="#d6d6d6")
    wrapper.pack(fill="both", expand=True)
    frame = tk.Frame(wrapper, bg=bg_color, bd=1, relief="solid")
    frame.place(relx=0.5, rely=0.5, anchor="center", width=1050, height=720)
    tk.Label(frame, text=title, bg=bg_color, font=("Segoe UI", 22, "bold"), fg="#333333").pack(pady=15)
    return frame


def add_top_nav(parent, target_func, label="⬅ BACK TO DASHBOARD"):
    nav_frame = tk.Frame(parent, bg=parent["bg"])
    nav_frame.pack(side="top", fill="x", padx=10, pady=5)
    tk.Button(nav_frame, text=label, font=("Arial", 9, "bold"), bg="#757575", fg="white", command=target_func).pack(
        side="left")


def styled_table(parent, cols):
    tree = ttk.Treeview(parent, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c);
        tree.column(c, anchor="center", width=140)
    tree.pack(fill="both", expand=True, padx=20, pady=10)
    return tree


# ================= ADMIN MODULES =================
def admin_dashboard():
    clear()
    frame = card("ADMIN CONTROL CENTER")
    grid = tk.Frame(frame, bg="#e0e0e0");
    grid.pack(pady=20)
    menu = [
        ("Manage Staff Approvals", approve_staff),
        ("View Registered Staff", view_staff),
        ("Master Timetable Setup", timetable_manager_ui),
        ("Daily Attendance Logs", view_attendance),
        ("Weekly Attendance Report", view_weekly_report),
        ("Import Staff (CSV)", import_staff),
        ("Export Today's Attendance", export_attendance),
        ("Logout", main_menu)
    ]
    for i, (txt, cmd) in enumerate(menu):
        tk.Button(grid, text=txt, width=35, height=2, font=("Arial", 10, "bold"), bg="#bdbdbd", command=cmd).grid(
            row=i // 2, column=i % 2, padx=15, pady=10)


def import_staff():
    """Import CSV: If password is missing, it creates 'Name123' as default."""
    f = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    if f:
        try:
            with open(f) as file:
                reader = csv.DictReader(file)
                count = 0
                for r in reader:
                    name = r.get('name', 'Unknown')
                    user = r.get('username', name.replace(" ", "").lower() + str(random.randint(10, 99)))
                    # Auto-generate password if not in CSV
                    pwd = r.get('password') if r.get('password') else f"{name.split()[0]}123"

                    try:
                        cursor.execute("INSERT INTO staff (name, username, password, approved) VALUES (?,?,?,1)",
                                       (name, user, pwd, 1))
                        count += 1
                    except sqlite3.IntegrityError:
                        pass
            conn.commit()
            messagebox.showinfo("Success", f"Imported {count} staff. Default passwords set as 'Name123' where missing.")
        except Exception as e:
            messagebox.showerror("File Error", "Ensure CSV has 'name' and 'username' headers.")


def approve_staff():
    clear();
    frame = card("Pending Approvals");
    add_top_nav(frame, admin_dashboard)
    tree = styled_table(frame, ("ID", "Name", "Username"))
    cursor.execute("SELECT id, name, username FROM staff WHERE approved=0")
    for r in cursor.fetchall(): tree.insert("", "end", values=r)

    def do_app():
        sel = tree.focus()
        if sel:
            s_id = tree.item(sel)["values"][0]
            cursor.execute("UPDATE staff SET approved=1 WHERE id=?", (s_id,))
            conn.commit();
            messagebox.showinfo("Success", "Approved.");
            approve_staff()

    tk.Button(frame, text="Approve Selected", bg="#4caf50", fg="white", command=do_app).pack(pady=10)


# ================= STAFF MODULES =================
def staff_portal_ui():
    clear();
    frame = card("Staff Portal");
    add_top_nav(frame, main_menu, label="⬅ RETURN TO HOME")
    tk.Label(frame, text="STAFF LOGIN", font=("Arial", 11, "bold"), bg="white").pack(pady=5)
    u_ent = tk.Entry(frame);
    u_ent.insert(0, "Username");
    u_ent.pack()
    p_ent = tk.Entry(frame, show="*");
    p_ent.pack(pady=5)

    def login():
        cursor.execute("SELECT id, approved FROM staff WHERE username=? AND password=?", (u_ent.get(), p_ent.get()))
        r = cursor.fetchone()
        if r and r[1]:
            staff_dashboard_main(r[0])
        elif r:
            messagebox.showwarning("Pending", "Account awaiting admin approval.")
        else:
            messagebox.showerror("Error", "Invalid credentials.")

    tk.Button(frame, text="Login", width=20, bg="#2196f3", fg="white", command=login).pack()

    tk.Label(frame, text="STAFF REGISTRATION", font=("Arial", 11, "bold"), bg="white").pack(pady=20)
    n_reg = tk.Entry(frame);
    n_reg.insert(0, "Full Name");
    n_reg.pack()
    u_reg = tk.Entry(frame);
    u_reg.insert(0, "Username");
    u_reg.pack(pady=5)
    p_reg = tk.Entry(frame, show="*");
    p_reg.pack()

    def register():
        try:
            cursor.execute("INSERT INTO staff (name, username, password, approved) VALUES (?,?,?,0)",
                           (n_reg.get(), u_reg.get(), p_reg.get()))
            conn.commit();
            messagebox.showinfo("Success", "Registered! Await Approval.");
            staff_portal_ui()
        except:
            messagebox.showerror("Error", "Username taken.")

    tk.Button(frame, text="Register", width=20, bg="#4caf50", fg="white", command=register).pack(pady=10)


def staff_dashboard_main(sid):
    clear();
    frame = card("Staff Workspace");
    add_top_nav(frame, main_menu, label="⬅ LOGOUT")
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT timestamp FROM attendance WHERE staff_id=? AND date=?", (sid, today))
    rec = cursor.fetchone()

    time_lbl = tk.Label(frame, font=("Arial", 35, "bold"), bg="white");
    time_lbl.pack(pady=10)

    def tick():
        time_lbl.config(text=datetime.now().strftime("%H:%M:%S")); root.after(1000, tick)

    tick()

    if not rec:
        tk.Button(frame, text="CLOCK IN", bg="#4caf50", fg="white", width=25, height=2,
                  command=lambda: mark_attendance_logic(sid)).pack()
    else:
        tk.Label(frame, text=f"Attendance marked at {rec[0]}", bg="white", fg="green").pack(pady=10)


def mark_attendance_logic(sid):
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")
    cursor.execute("INSERT INTO attendance (staff_id, timestamp, date, status) VALUES (?,?,?,?)",
                   (sid, now, today, "Present"))
    conn.commit();
    staff_dashboard_main(sid)


# ================= CLASS TIMETABLE VIEW =================
def classroom_timetable_viewer():
    clear();
    frame = card("Printable Class Timetables");
    add_top_nav(frame, main_menu)
    ctrl = tk.Frame(frame, bg="white");
    ctrl.pack(pady=10)
    class_box = ttk.Combobox(ctrl, values=CLASSES, width=10);
    class_box.grid(row=0, column=1);
    class_box.set("JSS1")

    def load():
        for w in table_fm.winfo_children(): w.destroy()
        selected = class_box.get()
        tree = ttk.Treeview(table_fm, columns=("Time", "Mon", "Tue", "Wed", "Thu", "Fri"), show="headings", height=12)
        tree.heading("Time", text="TIME SLOT");
        tree.column("Time", width=150)
        for d in DAYS: tree.heading(d[:3], text=d.upper()); tree.column(d[:3], width=130, anchor="center")
        for slot in SCHOOL_SLOTS:
            row = [slot]
            for d in DAYS:
                cursor.execute("SELECT subject FROM timetable WHERE class_name=? AND day=? AND slot_time=?",
                               (selected, d, slot))
                res = cursor.fetchone();
                row.append(res[0] if res else "---")
            tree.insert("", "end", values=row)
        tree.pack(fill="both", expand=True)

    tk.Button(ctrl, text="Generate Schedule", bg="#f57c00", fg="white", command=load).grid(row=0, column=2, padx=10)
    table_fm = tk.Frame(frame, bg="white");
    table_fm.pack(fill="both", expand=True, padx=20, pady=10)


# ================= ADDITIONAL ADMIN FUNCTIONS =================
def timetable_manager_ui():
    clear();
    frame = card("Timetable Setup");
    add_top_nav(frame, admin_dashboard)
    form = tk.Frame(frame, bg="white");
    form.pack(pady=10)
    sid = tk.Entry(form, width=5);
    sid.grid(row=0, column=1);
    tk.Label(form, text="Staff ID").grid(row=0, column=0)
    sub = tk.Entry(form, width=12);
    sub.grid(row=0, column=3);
    tk.Label(form, text="Subject").grid(row=0, column=2)
    cl_box = ttk.Combobox(form, values=CLASSES, width=8);
    cl_box.grid(row=0, column=5)
    dy_box = ttk.Combobox(form, values=DAYS, width=10);
    dy_box.grid(row=0, column=7)
    sl_box = ttk.Combobox(form, values=SCHOOL_SLOTS, width=15);
    sl_box.grid(row=0, column=9)

    def add():
        cursor.execute("INSERT INTO timetable (staff_id, subject, class_name, day, slot_time) VALUES (?,?,?,?,?)",
                       (sid.get(), sub.get(), cl_box.get(), dy_box.get(), sl_box.get()))
        conn.commit();
        timetable_manager_ui()

    tk.Button(form, text="Assign", command=add).grid(row=0, column=10, padx=5)
    tree = styled_table(frame, ("Staff", "Subject", "Class", "Day", "Slot"))
    cursor.execute(
        "SELECT staff.name, timetable.subject, timetable.class_name, timetable.day, timetable.slot_time FROM timetable JOIN staff ON staff.id = timetable.staff_id")
    for r in cursor.fetchall(): tree.insert("", "end", values=r)


def export_attendance():
    f = filedialog.asksaveasfilename(defaultextension=".csv")
    if f:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT staff.name, attendance.timestamp FROM attendance JOIN staff ON staff.id=attendance.staff_id WHERE attendance.date=?",
            (today,))
        with open(f, "w", newline="") as file:
            w = csv.writer(file);
            w.writerow(["Name", "Clock-In Time"]);
            w.writerows(cursor.fetchall())
        messagebox.showinfo("Success", "Exported.")


def view_weekly_report():
    clear();
    frame = card("Weekly Report");
    add_top_nav(frame, admin_dashboard)
    monday = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
    dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    tree = styled_table(frame, ["Staff Name"] + dates)
    cursor.execute("SELECT id, name FROM staff WHERE approved=1")
    for s_id, s_name in cursor.fetchall():
        row = [s_name]
        for d in dates:
            cursor.execute("SELECT id FROM attendance WHERE staff_id=? AND date=?", (s_id, d))
            row.append(" ✔ " if cursor.fetchone() else " ❌ ")
        tree.insert("", "end", values=row)


def view_staff():
    clear();
    frame = card("Staff Directory");
    add_top_nav(frame, admin_dashboard)
    tree = styled_table(frame, ("ID", "Name", "Username", "Password"))
    cursor.execute("SELECT id, name, username, password FROM staff")
    for r in cursor.fetchall(): tree.insert("", "end", values=r)

    def delete():
        s = tree.focus()
        if s: cursor.execute("DELETE FROM staff WHERE id=?", (tree.item(s)["values"][0],)); conn.commit(); view_staff()

    tk.Button(frame, text="Delete Selected", bg="red", fg="white", command=delete).pack(pady=5)


def view_attendance():
    clear();
    frame = card("Attendance Log");
    add_top_nav(frame, admin_dashboard)
    tree = styled_table(frame, ("Name", "Date", "Time"))
    cursor.execute(
        "SELECT staff.name, attendance.date, attendance.timestamp FROM attendance JOIN staff ON staff.id=attendance.staff_id")
    for r in cursor.fetchall(): tree.insert("", "end", values=r)


# ================= NAVIGATION =================
def main_menu():
    clear();
    frame = card("School Management System")
    tk.Button(frame, text="ADMINISTRATOR LOGIN", width=40, height=2, bg="#424242", fg="white",
              command=admin_login_ui).pack(pady=10)
    tk.Button(frame, text="STAFF PORTAL", width=40, height=2, bg="#2196f3", fg="white", command=staff_portal_ui).pack(
        pady=10)
    tk.Button(frame, text="CLASS TIMETABLES (JSS1 - SS3)", width=40, height=2, bg="#f57c00", fg="white",
              command=classroom_timetable_viewer).pack(pady=10)


def admin_login_ui():
    clear();
    frame = card("Admin Access");
    add_top_nav(frame, main_menu)
    u = tk.Entry(frame);
    u.insert(0, "admin");
    u.pack(pady=5);
    p = tk.Entry(frame, show="*");
    p.insert(0, "admin123");
    p.pack(pady=5)
    tk.Button(frame, text="Login", width=20,
              command=lambda: admin_dashboard() if u.get() == "admin" and p.get() == "admin123" else messagebox.showerror(
                  "Error", "Denied")).pack()


root = tk.Tk()
root.title("School Management Pro")
root.geometry("1150x780")
main_menu()
root.mainloop()