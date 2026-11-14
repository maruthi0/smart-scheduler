"""Styled error pages for 403, 404 and expired form tokens."""
from flask import render_template
from flask_wtf.csrf import CSRFError

from ..backend.services import NotFoundError, PermissionDenied


def _page(code, title, detail):
    return render_template("error.html", code=code, title=title, detail=detail), code


def register_error_pages(app):
    app.register_error_handler(NotFoundError, lambda e: _page(404, "Not found", str(e)))
    app.register_error_handler(PermissionDenied, lambda e: _page(403, "No access", str(e)))
    app.register_error_handler(404, lambda e: _page(
        404, "Page not found", "The address may be mistyped, or the page was removed."))
    app.register_error_handler(403, lambda e: _page(
        403, "No access", "Your account's role cannot open this page."))
    app.register_error_handler(CSRFError, lambda e: _page(
        400, "This form has expired", "Go back, reload the page and submit the form again."))
