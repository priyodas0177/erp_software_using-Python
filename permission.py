from flask import session
from database import get_connection


# ------------- Helper: Check Admin/User ------------------
def role_requered(role):
    return session.get("user_type") == role


#------------- Permission---------
def has_permission(feature_code):

    # ✅ Admin has all permissions
    if session.get("user_type") == "admin":
        return True

    # ✅ Normal user permission check
    user_id = session.get("user_id")
    if not user_id:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT is_allowed
        FROM user_permissions
        WHERE user_id=%s AND feature_code=%s
        LIMIT 1
    """, (user_id, feature_code))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return False

    return result[0] == 1
