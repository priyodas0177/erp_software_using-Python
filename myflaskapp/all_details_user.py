from flask import render_template, redirect, url_for, request,session
from database import get_connection
from permission import has_permission


def is_user_exist(username, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT id FROM users WHERE username=%s AND id<>%s", (username, user_id))
    else:
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row is not None


def is_email_exist(email,user_id=None):
    conn=get_connection()
    curser=conn.cursor()

    if user_id:
        curser.execute("SELECT id FROM users WHERE email=%s and id<>%s",
                       (email,user_id))
    else:
        curser.execute("SELECT id FROM users WHERE email=%s",(email,))
    email_result=curser.fetchone()
    curser.close()
    conn.close()
    return email_result is not None
def get_dispaly_name():
    return session.get("admin_name") or session.get("user_name") or "User"

def init_user_create_routes(app):
    @app.route("/admin/create_user", methods=["GET", "POST"])
    def create_user():
        if not session.get("user_type"):
            return redirect(url_for("login_page", expired=1))

        # ✅ allow admin OR create_user permission
        if not (session.get("user_type") == "admin" or has_permission("create_user")):
            return redirect(url_for("dashboard"))

        error = None
        success = None

        if request.method == "POST":
            fullname = request.form.get("fullname", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            email_input = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()
            gender = request.form.get("gender", "")
            role = request.form.get("role", "")

            DOMAIN = "@abc.com"
            if email_input and "@" not in email_input:
                email = email_input + DOMAIN
            else:
                email = email_input

            if not fullname or not username or not password or not email:
                error = "please fill all the fields."
            elif is_user_exist(username):
                error = "Username already exist. please choose a different username."
            elif is_email_exist(email):
                error = "Email already exist. please choose a different email."
            elif (not phone.isdigit()) or (len(phone) != 11):
                error = "Invalid phone number. please enter a valid 11-digit phone number."
            elif gender not in ["Male", "Female", "Others"]:
                error = "Invalid Gender."
            elif role not in ["Admin", "Employee", "Manager", "HR"]:
                error = "Invalid Role."
            else:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (fullname, username, password, email, phone, gender, role, is_active)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (fullname, username, password, email, phone, gender, role, 1))
                conn.commit()
                cursor.close()
                conn.close()

                success = "User Created Successfully."

        return render_template("create_user.html", error=error, success=success, display_name=get_dispaly_name())



def init_user_update_routes(app):

    @app.route("/admin/update_user", methods=["GET", "POST"])
    def update_user():
        if not session.get("user_type"):
            return redirect(url_for("login_page", expired=1))

        # allow admin OR permission
        if not (session.get("user_type") == "admin" or has_permission("create_user")):
            return redirect(url_for("dashboard"))
        
        display_name=get_dispaly_name()

        error = None
        success = None
        result_user = None

        # Step-1: user_id can come from GET (?user_id=) or POST (hidden input)
        user_id = (request.args.get("user_id") or "").strip()
        if request.method == "POST":
            user_id = (request.form.get("user_id") or "").strip()

        # If no user_id yet -> just show search box
        if not user_id:
            return render_template("update_user.html",display_name=display_name, result_user=None, error=None, success=None)

        if not user_id.isdigit():
            return render_template("update_user.html", result_user=None,display_name=display_name,
                                   error="Please enter a valid numeric user id.", success=None)

        user_id = int(user_id)

        conn = get_connection()
        curser = conn.cursor()

        # Load user
        curser.execute("""
            SELECT id, fullname, username, password, email, phone, gender, role, is_active
            FROM users WHERE id=%s
        """, (user_id,))
        result_user = curser.fetchone()

        if not result_user:
            curser.close()
            conn.close()
            return render_template("update_user.html", result_user=None,display_name=display_name,
                                   error="User not found.", success=None)

        old_fullname= result_user[1]
        old_username= result_user[2]
        old_password= result_user[3]
        old_email= result_user[4]
        old_phone= result_user[5]
        old_gender= result_user[6]
        old_role= result_user[7]
        old_status= result_user[8]

        # Step-2: If POST -> update
        if request.method == "POST":
            
            conn = get_connection()
            curser = conn.cursor()
            fullname = request.form.get("fullname", "").strip() or old_fullname
            username = request.form.get("username", "").strip() or old_username
            password = request.form.get("password", "").strip()  # may be empty
            email    = request.form.get("email", "").strip() or old_email
            phone    = request.form.get("phone", "").strip() or old_phone
            gender   = request.form.get("gender", "").strip() or old_gender
            role     = request.form.get("role", "").strip() or old_role
            status=request.form.get("status", "") or old_status
            is_active=1 if status =="Active" else 0

            final_password = password if password else old_password

            # No change check 
            if (
                fullname==old_fullname and username==old_username and 
                final_password==old_password and email==old_email and
                phone==old_phone and gender==old_gender and role==old_role and status==old_status 
            ):
                error="No data was changed."
                success=None

            #others validation
            elif not fullname or not username or not email:
                error = "fullname, username, email cannot be empty."
            elif is_user_exist(username, user_id):
                error="Username already exist. please choose a different username."
            elif is_email_exist(email, user_id):
                error="Email already exist. please choose a different Email."
            elif phone and ((not phone.isdigit()) or (len(phone) != 11)):
                error = "Invalid phone number. Must be 11 digit number."
            elif gender not in ["Male", "Female", "Others"]:
                error = "Invalid Gender."
            elif role not in ["Admin", "Employee", "Manager", "HR"]:
                error = "Invalid Role."
            else:
                curser.execute("""
                    UPDATE users
                    SET fullname=%s, username=%s, password=%s,
                        email=%s, phone=%s, gender=%s, role=%s, is_active=%s
                    WHERE id=%s
                """, (fullname, username, final_password, email, phone, gender, role, is_active, user_id))
                conn.commit()
                #success=  "User Updated Successfully."
                error=None
                return redirect(url_for("update_user", success=  "User Updated Successfully.")) 
                 
                #result_user=(user_id, "","","","","","","") # clear boxes after success (your requirement)
               


                # reload updated user
                # curser.execute("""
                #     SELECT id, fullname, username, password, email, phone, gender, role
                #     FROM users WHERE id=%s
                # """, (user_id,))
                #result_user = curser.fetchone()

            curser.close()
            conn.close()

        return render_template("update_user.html",display_name=get_dispaly_name(),
        user_id=user_id, result_user=result_user, error=error,success=success )



