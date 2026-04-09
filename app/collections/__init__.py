from flask import Blueprint
bp = Blueprint('collections', __name__)
from app.collections import routes
