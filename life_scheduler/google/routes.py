from flask import Blueprint, current_app, url_for, session, redirect, request, abort
from flask_login import login_required, current_user
from requests_oauthlib import OAuth2Session

from life_scheduler.auth.google import get_google_provider_config
from life_scheduler.auth.utils import approval_required
from life_scheduler.google.models import Google

blueprint = Blueprint("google", __name__, url_prefix="/google")


@blueprint.route("/login/")
@login_required
@approval_required
def login():
    provider_config = get_google_provider_config()
    authorization_url = provider_config["authorization_endpoint"]

    client_id = current_app.config["GOOGLE_CLIENT_ID"]
    scope = [
        "email",
        "https://www.googleapis.com/auth/calendar",
    ]
    redirect_uri = url_for("google.login_callback", _external=True)

    oauth = OAuth2Session(
        client_id=client_id,
        scope=scope,
        redirect_uri=redirect_uri,
    )

    url, state = oauth.authorization_url(
        url=authorization_url,
        access_type="offline",
        prompt="consent",
    )

    current_app.logger.info(f"url = {url}")

    session["oauth_state"] = state
    return redirect(url)


@blueprint.route("/login/callback/")
@login_required
@approval_required
def login_callback():
    code = request.args.get("code")

    provider_config = get_google_provider_config()
    token_url = provider_config["token_endpoint"]

    client_id = current_app.config["GOOGLE_CLIENT_ID"]
    client_secret = current_app.config["GOOGLE_CLIENT_SECRET"]

    oauth = OAuth2Session(
        client_id=client_id,
        state=session["oauth_state"],
        redirect_uri=request.base_url,
    )

    token = oauth.fetch_token(
        token_url=token_url,
        client_secret=client_secret,
        authorization_response=request.url,
        code=code,
    )

    user_info = oauth.get("https://openidconnect.googleapis.com/v1/userinfo").json()

    google = Google(
        token=token,
        email=user_info["email"],
        user=current_user,
    )

    Google.create(google)

    return redirect(url_for("board.settings"))


@blueprint.route("/logout/<google_id>/")
@login_required
@approval_required
def logout(google_id):
    google = Google.get_by_id(google_id)

    if google.user.id != current_user.id:
        abort(403)

    Google.remove(google)
    return redirect(url_for("board.settings"))
