from flask import Blueprint
bp = Blueprint('dm', __name__)
from app.dm import routes
