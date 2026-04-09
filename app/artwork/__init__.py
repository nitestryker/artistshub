from flask import Blueprint

bp = Blueprint('artwork', __name__)

from app.artwork import routes
