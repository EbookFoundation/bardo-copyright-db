from flask import (
    Blueprint, request, session, url_for, redirect, current_app, jsonify
)

from model.cce import CCE

bp = Blueprint('base', __name__, url_prefix='/')

APP_VERSION = 'v0.1'

@bp.route('/')
def query():
    return redirect(url_for('flasgger.apidocs'))
