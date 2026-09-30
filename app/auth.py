"""Registration, login and logout, plus role-based access helpers."""
from flask import (
    Blueprint, abort, current_app, flash, g, redirect, render_template, request, session,
    url_for,
)

from .models import COORDINATOR, ROLES, User, db
from .services import ValidationError, authenticate, register_user

bp = Blueprint("auth", __name__)


@bp.before_app_request
def load_current_user():
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None


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


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        form = request.form
        role = form.get("role")
        if role == COORDINATOR and form.get("coordinator_code") != current_app.config["COORDINATOR_CODE"]:
            flash("Invalid coordinator access code.", "error")
            return render_template("register.html", roles=ROLES, form=form)
        try:
            user = register_user(form.get("username"), form.get("password"), role,
                                 form.get("full_name"))
        except ValidationError as e:
            flash(str(e), "error")
            return render_template("register.html", roles=ROLES, form=form)
        session.clear()
        session["user_id"] = user.id
        return redirect(url_for("auth.home"))
    return render_template("register.html", roles=ROLES, form={})


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = authenticate(request.form.get("username"), request.form.get("password"))
        if user:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("auth.home"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
