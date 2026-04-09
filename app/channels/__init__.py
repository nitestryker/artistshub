from flask import Blueprint

bp = Blueprint('channels', __name__)

from app.channels import routes
