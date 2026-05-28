"""routes/__init__.py"""
from flask import Blueprint

main_bp = Blueprint('main', __name__)

from . import main_routes  # noqa: F401, E402
