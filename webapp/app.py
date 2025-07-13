from typing import List
from csv import Error
import json
from typing import Dict, Optional, Union
from flask import Flask
from flask import request
from flask_cors import CORS
from markupsafe import escape

from webapp.web.data.nodes.user import User, Node, Image, Descriptor, PID, NodeFactory

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
    try:
        user = User.login(user_name=escape(username), password=escape(password))
    except AssertionError as e:
        print(f"Logging error for username: {username}")
    finally:
        if user is None:
            return {"success": "no"}

    return {"success": "yes"} | json.loads(user.serialize())


@app.route("/register", methods=["GET", "POST"])
def register():
    user: Optional[User] = None
    username: Optional[str] = request.json.get("username")  # type: ignore
    password: Optional[str] = request.json.get("password")  # type: ignore
    try:
        user = User.login(user_name=escape(username), password=escape(password))
    except AssertionError as e:
        print(f"Login error, user doesn't seem to exist: {username}")
        print("Registering user")

    if user is None:
        try:
            user = User.register(user_name=escape(username), password=escape(password))
            return {"success": "yes", "existence": "no"} | json.loads(user.serialize())
        except AssertionError as e:
            print(f"Error registering user: {username}")
            return {"success": "no", "existence": "no"}

    return {"success": "yes", "existence": "yes"} | json.loads(user.serialize())


@app.route("/upload", methods=["POST"])
def upload_image():
    user: Optional[Node] = None
    userid: Optional[str] = request.form.get("userid")  # type: ignore
    if userid is None:
        return {"success": "no", "message": "Userid not passed"}
    user = Node.from_id(userid, NodeFactory())
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


@app.route("/add_descriptor", methods=["POST"])
def add_descriptor():
    user: Optional[Node] = None
    userid: Optional[str] = request.form.get("userid")  # type: ignore
    if userid is None:
        return {"success": "no", "message": "Userid not passed"}
    user = Node.from_id(userid, NodeFactory())
    if user is None:
        return {
            "success": "no",
            "message": f"User not found, check the userid passed: {userid}",
        }

    assert isinstance(user, User)
    descriptor_name: Optional[str] = request.form.get("descriptor_name")
    if descriptor_name is None:
        return {"success": "no", "message": "Descriptor name not passed"}
    descriptor: Descriptor = Descriptor(name=descriptor_name)
    User.consume(user, descriptor)
    return (
        {"success": "yes"}
        | {"userid": user.id.serialize()}
        | {"descriptorid": descriptor.id.serialize()}
    )


@app.route("/get_asset_tree", methods=["GET", "POST"])
def get_asset_tree():
    """
    Get all the information required to display the asset tree for a user.
    This includes: level sorted nodes, asset/descriptor names, and parent-child relationships.
    """
    user: Optional[Node] = None
    userid: Optional[str] = request.json.get("userid")  # type: ignore
    if userid is None:
        return {"success": "no", "message": "Userid not passed"}
    user = Node.from_id(PID.deserialize(userid), NodeFactory())
    if user is None:
        return {
            "success": "no",
            "message": f"User not found, check the userid passed: {userid}",
        }
    assert isinstance(user, User)
    nodes_info: List[Dict[str, Union[str, int]]] = (
        user.get_asset_tree_info_for_visualization()
    )
    return {
        "success": "yes",
        "message": "Asset tree information retrieved successfully",
        "nodes_info": nodes_info,
    }
