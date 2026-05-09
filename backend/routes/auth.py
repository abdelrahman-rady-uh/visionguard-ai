import functools
import logging

from flask import Blueprint, session, redirect, url_for, jsonify, current_app, render_template
from authlib.integrations.flask_client import OAuth

from backend.database import Database

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)
oauth = OAuth()
_google = None
db = Database()


def init_auth(app):
    """Register Google OAuth with the Flask app. Call after app creation."""
    global _google
    oauth.init_app(app)
    _google = oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID", ""),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET", ""),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


# ── OAuth routes ───────────────────────────────────────────────────────────────

def _oauth_configured():
    cid = current_app.config.get("GOOGLE_CLIENT_ID", "")
    return bool(cid) and not cid.startswith("your-")


@auth_bp.route("/auth/google")
def google_login():
    if not _oauth_configured():
        return redirect("/?oauth_notice=1")
    redirect_uri = url_for("auth.google_callback", _external=True)
    return _google.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/callback")
def google_callback():
    token = _google.authorize_access_token()
    user_info = token.get("userinfo") or {}

    google_id = user_info.get("sub", "")
    email = user_info.get("email", "")
    name = user_info.get("name") or email
    picture = user_info.get("picture", "")

    if not google_id or not email:
        logger.warning("Google callback missing sub/email in userinfo: %s", user_info)
        return redirect("/")

    try:
        user_id = db.get_or_create_google_user(google_id, email, name, picture)
    except Exception as exc:
        logger.error("Failed to create/get Google user: %s", exc)
        return redirect("/")

    session.permanent = True
    session["user_id"] = user_id
    session["user_email"] = email
    session["user_name"] = name
    session["user_picture"] = picture

    return redirect("/upload")


@auth_bp.route("/auth/logout")
def logout():
    session.clear()
    return redirect("/")


# ── API routes ─────────────────────────────────────────────────────────────────

@auth_bp.route("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"authenticated": False}), 200
    return jsonify({
        "authenticated": True,
        "user_id": session["user_id"],
        "email": session.get("user_email"),
        "name": session.get("user_name"),
        "picture": session.get("user_picture"),
    })


@auth_bp.route("/api/my-history")
@login_required
def my_history_api():
    user_id = session["user_id"]
    try:
        history = db.get_user_history(user_id)
        return jsonify({"history": history})
    except Exception as exc:
        logger.error("get_user_history failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@auth_bp.route("/api/analysis-result/<int:video_id>")
@login_required
def get_analysis_result(video_id):
    user_id = session["user_id"]
    try:
        data = db.get_full_analysis_result(video_id, user_id)
        if not data:
            return jsonify({"error": "Not found or access denied"}), 404
        return jsonify(data)
    except Exception as exc:
        logger.error("get_full_analysis_result failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ── Page route ─────────────────────────────────────────────────────────────────

@auth_bp.route("/my-history")
def history_page():
    return render_template("my_history.html")
