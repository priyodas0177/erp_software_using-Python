from flask import Flask, render_template, session, redirect, url_for
from database import get_connection
from all_details_user import has_permission

def get_dispaly_name():
    return session.get("admin_name") or session.get("user_name") or "User"
def init_user_list_routes(app):
    @app.route("/admin/show_users")
    def show_users():

        display_name=get_dispaly_name()
      

        # ✅ Safe way (avoid KeyError)
        user_id = session.get("user_id")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, fullname, username, email,
                   phone, gender, role
            FROM users
            WHERE id = %s
        """, (user_id,))

        users = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("show_users.html", users=users, display_name=display_name)
