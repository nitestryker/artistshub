from flask import Blueprint

bp = Blueprint('donate', __name__)

from app.donate import routes
