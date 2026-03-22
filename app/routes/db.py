"""
Database connection helper.

Uses Flask's application context (g) to ensure each request gets exactly
one connection that is automatically closed when the request ends —
even if an exception is raised mid-request.
"""
import sqlite3
from flask import g, current_app


def get_db():
    """
    Return the request-scoped database connection.
    Creates it on first call within a request, reuses it on subsequent calls.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE_PATH'])

        # FIX 2: Row objects now support column access by name
        #         e.g. row['name'] or row.keys() — required for templates
        g.db.row_factory = sqlite3.Row

        # FIX 4: Foreign key enforcement must be set per connection in SQLite
        g.db.execute('PRAGMA foreign_keys = ON')

    return g.db


def close_db(e=None):
    """
    Close the database connection at the end of the request.
    Registered with Flask via init_app(); called automatically on teardown.
    The optional argument `e` is the exception (if any) — we don't need it.
    """
    # FIX 3: g.pop() safely removes the connection whether or not it exists,
    #         and closes it — even when an exception ended the request early.
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app):
    """Register the teardown hook with the Flask application."""
    app.teardown_appcontext(close_db)