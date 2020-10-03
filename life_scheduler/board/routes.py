from flask import Blueprint, render_template
from flask_login import login_required, current_user

from life_scheduler.auth.utils import approval_required

blueprint = Blueprint("board", __name__, url_prefix="/board")


@blueprint.route("/")
@login_required
@approval_required
def index():
    return current_user.trello.get("https://trello.com/1/members/me/boards/")
