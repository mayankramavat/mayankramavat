import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_setup import init_db, create_user, authenticate_user

app = Flask(__name__)
app.secret_key = "focuspulse_super_secret_key"

DATABASE = "focuspulse.db"

# Initialize database
init_db()


# ------------------------------
# DATABASE CONNECTION HELPER
# ------------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------
# LOGIN REQUIRED DECORATOR
# ------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------
# HOME ROUTE
# ------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ------------------------------
# OPTIONAL INFO PAGES
# ------------------------------
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/how-it-works")
def how_it_works():
    return render_template("howitworks.html")


@app.route("/benefits")
def benefits():
    return render_template("benefits.html")


@app.route("/team")
def team():
    return render_template("team.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# ------------------------------
# SIGNUP ROUTE
# ------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("signup"))

        user_id = create_user(username, email, password)
        if user_id:
            session["user_id"] = user_id
            session["user_name"] = username
            flash(f"Signup successful! Welcome, {username}", "success")
            return redirect(url_for("home"))
        else:
            flash("Username or Email already exists", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")


# ------------------------------
# LOGIN ROUTE
# ------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form["username"].strip()
        password = request.form["password"]

        user = authenticate_user(username_or_email, password)
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["username"]
            flash(f"Login successful! Welcome back, {user['username']}", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username/email or password", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


# ------------------------------
# LOGOUT ROUTE
# ------------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "success")
    return redirect(url_for("home"))


# ------------------------------
# PLANNER ROUTE
# ------------------------------
@app.route("/planner", methods=["GET", "POST"])
@login_required
def planner():
    user_id = session["user_id"]
    conn = get_db_connection()

    if request.method == "POST":
        task_title = request.form["task_title"].strip()
        subject = request.form["subject"].strip()
        deadline = request.form["deadline"].strip()
        status = request.form["status"].strip()

        if task_title and subject and deadline and status:
            conn.execute(
                """
                INSERT INTO tasks (user_id, task_title, subject, deadline, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, task_title, subject, deadline, status)
            )
            conn.commit()
            flash("Task added successfully.", "success")
        else:
            flash("All task fields are required.", "error")

        conn.close()
        return redirect(url_for("planner"))

    tasks = conn.execute(
        """
        SELECT * FROM tasks
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,)
    ).fetchall()

    conn.close()
    return render_template("planner.html", tasks=tasks)


# ------------------------------
# DELETE TASK ROUTE
# ------------------------------
@app.route("/delete-task/<int:task_id>")
@login_required
def delete_task(task_id):
    user_id = session["user_id"]
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    conn.commit()
    conn.close()

    flash("Task deleted successfully.", "success")
    return redirect(url_for("planner"))


# ------------------------------
# UPDATE STATUS ROUTE
# ------------------------------
@app.route("/update-status/<int:task_id>", methods=["POST"])
@login_required
def update_status(task_id):
    user_id = session["user_id"]
    new_status = request.form["status"]

    conn = get_db_connection()
    conn.execute(
        "UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?",
        (new_status, task_id, user_id)
    )
    conn.commit()
    conn.close()

    flash("Task status updated successfully.", "success")
    return redirect(url_for("planner"))


# ------------------------------
# DASHBOARD ROUTE
# ------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    conn = get_db_connection()

    total_tasks = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE user_id = ?",
        (user_id,)
    ).fetchone()["count"]

    completed_tasks = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE user_id = ? AND status = 'Completed'",
        (user_id,)
    ).fetchone()["count"]

    pending_tasks = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE user_id = ? AND status = 'Pending'",
        (user_id,)
    ).fetchone()["count"]

    in_progress_tasks = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE user_id = ? AND status = 'In Progress'",
        (user_id,)
    ).fetchone()["count"]

    recent_tasks = conn.execute(
        """
        SELECT * FROM tasks
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (user_id,)
    ).fetchall()

    conn.close()

    productivity_score = 0
    if total_tasks > 0:
        productivity_score = round((completed_tasks / total_tasks) * 100)

    return render_template(
        "dashboard.html",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        productivity_score=productivity_score,
        recent_tasks=recent_tasks
    )


# ------------------------------
# FOCUS MODE ROUTE
# ------------------------------
@app.route("/focus")
@login_required
def focus():
    user_id = session["user_id"]
    conn = get_db_connection()

    tasks = conn.execute(
        """
        SELECT task_title FROM tasks
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,)
    ).fetchall()

    recent_sessions = conn.execute(
        """
        SELECT * FROM focus_sessions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (user_id,)
    ).fetchall()

    conn.close()
    return render_template("focus.html", tasks=tasks, recent_sessions=recent_sessions)


# ------------------------------
# SAVE FOCUS SESSION ROUTE
# ------------------------------
@app.route("/save-focus-session", methods=["POST"])
@login_required
def save_focus_session():
    user_id = session["user_id"]
    task_title = request.form.get("task_title", "").strip()
    duration = request.form.get("duration", "0").strip()
    distraction_count = request.form.get("distraction_count", "0").strip()
    focus_score = request.form.get("focus_score", "0").strip()
    notes = request.form.get("notes", "").strip()

    try:
        duration = int(duration)
        distraction_count = int(distraction_count)
        focus_score = int(focus_score)
    except ValueError:
        flash("Invalid focus session data.", "error")
        return redirect(url_for("focus"))

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO focus_sessions (user_id, task_title, duration, distraction_count, focus_score, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, task_title, duration, distraction_count, focus_score, notes)
    )
    conn.commit()
    conn.close()

    flash("Focus session saved successfully!", "success")
    return redirect(url_for("focus"))


# ------------------------------
# DELETE FOCUS SESSION ROUTE
# ------------------------------
@app.route("/delete-focus-session/<int:session_id>")
@login_required
def delete_focus_session(session_id):
    user_id = session["user_id"]
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM focus_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    )
    conn.commit()
    conn.close()

    flash("Focus session deleted successfully.", "success")
    return redirect(url_for("focus"))

    # ------------------------------
# WELLNESS SETUP ROUTE
# ------------------------------
@app.route("/wellness")
@login_required
def wellness():
    user_id = session["user_id"]
    conn = get_db_connection()

    recent_wellness = conn.execute(
        """
        SELECT * FROM wellness_sessions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (user_id,)
    ).fetchall()

    conn.close()
    return render_template("wellness.html", recent_wellness=recent_wellness)


# ------------------------------
# WELLNESS TIMER PAGE
# ------------------------------
@app.route("/wellness-timer")
@login_required
def wellness_timer():
    return render_template("wellness_timer.html")


# ------------------------------
# SAVE WELLNESS SESSION
# ------------------------------
@app.route("/save-wellness-session", methods=["POST"])
@login_required
def save_wellness_session():
    user_id = session["user_id"]

    active_minutes = request.form.get("active_minutes", "0").strip()
    active_seconds = request.form.get("active_seconds", "30").strip()
    rest_seconds = request.form.get("rest_seconds", "10").strip()
    rounds = request.form.get("rounds", "1").strip()
    completed_rounds = request.form.get("completed_rounds", "0").strip()
    total_active_time = request.form.get("total_active_time", "0").strip()

    try:
        active_minutes = int(active_minutes)
        active_seconds = int(active_seconds)
        rest_seconds = int(rest_seconds)
        rounds = int(rounds)
        completed_rounds = int(completed_rounds)
        total_active_time = int(total_active_time)
    except ValueError:
        flash("Invalid wellness session data.", "error")
        return redirect(url_for("wellness"))

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO wellness_sessions
        (user_id, active_minutes, active_seconds, rest_seconds, rounds, completed_rounds, total_active_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, active_minutes, active_seconds, rest_seconds, rounds, completed_rounds, total_active_time, "Completed")
    )
    conn.commit()
    conn.close()

    flash("Wellness session saved successfully!", "success")
    return redirect(url_for("wellness"))

if __name__ == "__main__":
    app.run(debug=True)
