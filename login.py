from database import get_connection
from datetime import timedelta, date
from flask import Flask, render_template, request, redirect, url_for, session
from permission import has_permission, role_requered
from all_details_user import init_user_create_routes, init_user_update_routes
from attendance import log_login,log_logout
from show_user import init_user_list_routes

app = Flask(__name__)
app.secret_key = "abcd"
app.permanent_session_lifetime = timedelta(minutes=15)

init_user_create_routes(app)
init_user_update_routes(app)
init_user_list_routes(app)


# ------------------ Home ------------------
@app.route("/")
def home():
    return redirect(url_for("login_page"))

from datetime import datetime

@app.before_request
def idle_timeout():
    # allow login + static without checks
    if request.endpoint in ("login_page", "static"):
        return

    # if not logged in, nothing to do
    if not session.get("user_type"):
        return

    now = datetime.now().timestamp()
    last_activity = session.get("last_activity")

    # first request after login
    if last_activity is None:
        session["last_activity"] = now
        return

    # if inactive more than 5 minutes => logout
    if now - last_activity > 5 * 60:
        session.clear()
        return redirect(url_for("login_page", expired=1))

    # update activity time (refresh)
    session["last_activity"] = now
    session.modified = True


# ------------------ Login ------------------
@app.route("/login", methods=["GET", "POST"])
def login_page():
    message = None

    if request.args.get("expired") == "1":
        message = "Session expired. Please login again."

    if request.method == "POST":
        session.clear()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # ----------- Try admin ----------
        conn = get_connection()
        cursor = conn.cursor()

        # 1) check admin (active or inactive)
        cursor.execute("""
            SELECT id, name, is_active
            FROM admin
            WHERE (name=%s OR email=%s) AND password=%s
        """, (username, username, password))

        result_admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if result_admin:
            admin_id, admin_name, is_active = result_admin

            if is_active == 0:
                return render_template("login.html", message="Your account is disabled.")

            session.clear()
            session.permanent = True
            session["user_type"] = "admin"
            session["admin_id"] = admin_id
            session["admin_name"] = admin_name
            session.modified = True
            return redirect(url_for("dashboard"))

        # ----------- Try Users ----------
        conn = get_connection()
        cursor = conn.cursor()

        # 2) check user (active or inactive)
        cursor.execute("""
            SELECT id, username, role, is_active
            FROM users
            WHERE (username=%s OR email=%s) AND password=%s
        """, (username, username, password))

        result_user = cursor.fetchone()

        if result_user:
            user_id, user_name, role, is_active = result_user

            if is_active == 0:
                cursor.close()
                conn.close()
                return render_template("login.html", message="Your account is inactive.")

            session.clear()
            session.permanent = True
            session["user_type"] = "user"
            session["user_id"] = user_id
            session["user_name"] = user_name
            session["role"] = role
            session["last_activity"] = datetime.now().timestamp()
            session.modified = True

            log_login(conn, user_id)

            cursor.close()
            conn.close()
            return redirect(url_for("dashboard"))

        cursor.close()
        conn.close()
        return render_template("login.html", message="Invalid username or password.")

    return render_template("login.html", message=message)


#---------------Display name -------------
def get_dispaly_name():
    return session.get("admin_name") or session.get("user_name") or "User"


# -------------- Admin Dashboard ------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("user_type"):
        return redirect(url_for("login_page", expired=1))
    
    return render_template(
        "dashboard.html",
        display_name=get_dispaly_name()
    )


@app.context_processor
def inject_permission():
    return dict(has_permission=has_permission)

#------------- Search User -------------
@app.route("/admin/search-user", methods=["GET", "POST"])
def search_user():
    if not session.get("user_type"):
        return redirect(url_for("login_page", expired=1))

    if not (
        session.get("user_type") == "admin"
        or has_permission("give_permission")
        ):
        return redirect(url_for("dashboard"))
    
    user = None
    error = None
    features = []
    allowed_map = {}

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT feature_code, feature_name FROM features") #show checkbox data.
    features = cursor.fetchall()

    # user_id from GET or POST
    user_id = (request.args.get("user_id") or "").strip()
    if request.method == "POST":
        user_id = (request.form.get("user_id") or "").strip()

    if user_id:
        cursor.execute("SELECT id, username, email FROM users WHERE id=%s", (user_id,)) #search with user. 
        user = cursor.fetchone()

        if not user:
            error = "User not found. please enter valid user id."
        else:
            cursor.execute("""
                SELECT feature_code, is_allowed
                FROM user_permissions
                WHERE user_id=%s
            """, (user[0],))
            allowed_map = {code: is_allowed for code, is_allowed in cursor.fetchall()} #if permissson =1 checkbox check, elso uncheck

    cursor.close()
    conn.close()

    return render_template( #send data to html
        "search_user.html",
        user=user,
        error=error,
        features=features,
        allowed_map=allowed_map,
        display_name=get_dispaly_name()
    )



#------------- Save Permissions -------------
@app.route("/admin/save-permissions/<int:user_id>", methods=["POST"])
def save_permissions(user_id):

    if not session.get("user_type"):
        return redirect(url_for("login_page", expired=1))

    # allow admin OR permission
    if not (session.get("user_type") == "admin" or has_permission("give_permission")):
        return redirect(url_for("dashboard"))

    selected = request.form.getlist("feature_codes")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # reset permissions
        cursor.execute(
            "UPDATE user_permissions SET is_allowed=0 WHERE user_id=%s",
            (user_id,)
        )

        for code in selected:
            cursor.execute("""
                UPDATE user_permissions
                SET is_allowed=1
                WHERE user_id=%s AND feature_code=%s
            """, (user_id, code))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO user_permissions (user_id, feature_code, is_allowed)
                    VALUES (%s, %s, 1)
                """, (user_id, code))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

    # ✅ redirect back to same user page (important)
    return redirect(url_for("search_user", user_id=user_id))






@app.route("/attendance")
def attendance():
    if not session.get("user_type"):
        return redirect(url_for("login_page", expired=1))
    

    user_id = session["user_id"]

    # ✅ last 30 days (1 month)
    start_date = date.today() - timedelta(days=30)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, att_date, in_time, out_time, stay_minutes, status, remarks
        FROM attendance_daily
        WHERE user_id=%s AND att_date >= %s
        ORDER BY att_date DESC
    """, (user_id, start_date))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("attendance.html", rows=rows, start_date=start_date, display_name=get_dispaly_name())




# ------------------ Logout ------------------
@app.route("/logout")
def logout():
    if session.get("user_type") == "user":
        user_id = session.get("user_id")
        conn = get_connection()
        log_logout(conn, user_id)
        conn.close()

    session.clear()
    return redirect(url_for("login_page"))


# ------------------ Run Server ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
