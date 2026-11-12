"""Login and logout, plus role-based access helpers. Accounts are pre-assigned."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for

from ..backend import services
from ..backend.models import User, db

bp = Blueprint("auth", __name__)

ALLOWED_BEFORE_PASSWORD_CHANGE = ("auth.change_password", "auth.logout", "static")


@bp.before_app_request
def load_current_user():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    if user and session.get("token") != user.session_token:
        session.clear()
        user = None
    g.user = user
    if (user and user.must_change_password
            and request.endpoint not in ALLOWED_BEFORE_PASSWORD_CHANGE):
        return redirect(url_for("auth.change_password"))
    return None


def _start_session(user):
    session.clear()
    session["user_id"] = user.id
    session["token"] = user.session_token
    session.permanent = True


def require_role(role):
    """Call from a blueprint's before_request to restrict it to one role."""
    if g.user is None:
        return redirect(url_for("auth.login"))
    if g.user.role != role:
        abort(403)
    return None


@bp.route("/")
def home():
    if g.user is None:
        return redirect(url_for("auth.login"))
    if g.user.is_coordinator:
        return redirect(url_for("coordinator.dashboard"))
    return redirect(url_for("instructor.dashboard"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            user = services.authenticate(request.form.get("username"),
                                         request.form.get("password"))
        except services.TooManyAttempts as e:
            flash(str(e), "error")
            return render_template("login.html"), 429
        if user:
            _start_session(user)
            return redirect(url_for("auth.home"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@bp.route("/password", methods=["GET", "POST"])
def change_password():
    if g.user is None:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        form = request.form
        try:
            services.change_password(g.user, form.get("current_password"),
                                     form.get("new_password"), form.get("confirm_password"))
        except services.ValidationError as e:
            flash(str(e), "error")
        else:
            _start_session(g.user)  # the old token stopped matching when the password changed
            flash("Your password was changed.", "success")
            return redirect(url_for("auth.home"))
    return render_template("change_password.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
