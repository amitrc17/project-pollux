from csv import Error
import json
from typing import Optional
from flask import Flask
from flask import request
from flask_cors import CORS
from markupsafe import escape

from .web.data.asset_forest import User

app = Flask(__name__)
CORS(app, origins="*")


@app.route("/message")
def hello():
    return {"message": "Have fun"}


@app.route("/login", methods=["GET", "POST"])
def login():
    user: Optional[User] = None
    username: Optional[str] = request.json.get("username")  # type: ignore
    password: Optional[str] = request.json.get("password")  # type: ignore
    print(f"Logging for request params: {request.json}")
    try:
        user = User.login(user_name=escape(username), password=escape(password))
    except AssertionError as e:
        print(f"Logging error for username: {username}")
    finally:
        if user is None:
            return {"success": "no"}

    return {"success": "yes"} | json.loads(user.serialize())
