from typing import List
from csv import Error
import json
from typing import Optional
from flask import Flask
from flask import request
from flask_cors import CORS
from markupsafe import escape

from .web.data.asset_forest import User, Node, Image

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


@app.route("/upload", methods=["POST"])
def upload_image():
    user: Optional[Node] = None
    userid: Optional[str] = request.form.get("userid")  # type: ignore
    if userid is None:
        return {"success": "no", "message": "Userid not passed"}
    user = Node.from_id(userid)
    if user is None:
        return {"success": "no", "message": "User not found, check the userid passed"}

    assert isinstance(user, User)
    all_images: List[Image] = user.get_images()
    print(f"Total images found: {len(all_images)}")
    print(f"Image sizes: {[len(img.image_data) for img in all_images]}")
    file = request.files["file"].stream
    print(f"Uploading image for user: {user.id.serialize()}")
    image: Image = user.attach_image(image_file_buffer=file)  # type: ignore

    if image is None:
        return {"success": "no", "message": "Failed to upload image"}

    print(f"Image uploaded with id: {image.id.serialize()}")
    return {"success": "yes"} | json.loads(image.serialize())
