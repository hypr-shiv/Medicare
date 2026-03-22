"""
Smart Hospital Management System - Entry Point
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == "__main__":
    host  = os.environ.get("FLASK_HOST", "127.0.0.1")
    port  = int(os.environ.get("FLASK_PORT", 5000))
    debug = app.config.get("DEBUG", False)
    app.run(host=host, port=port, debug=debug)
