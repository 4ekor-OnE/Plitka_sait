# -*- coding: utf-8 -*-
"""WSGI entry point for Phusion Passenger. Exposes ``application`` (Flask app)."""
import os
import sys

os.environ.setdefault("DISABLE_SOCKETIO", "1")

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import app as application
