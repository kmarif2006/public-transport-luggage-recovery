from flask import Blueprint, render_template, request, redirect, url_for, flash
from backend.extensions import mongo
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/depot-login", methods=["GET","POST"])
def depot_login():

    if request.method == "POST":

        depot_id = request.form["depot_id"]
        password = request.form["password"]

        user = mongo.db.users.find_one({
            "depot_id": depot_id,
            "role": "manager"
        })

        if user and check_password_hash(user["password"], password):
            return redirect(url_for("manager.dashboard"))

        flash("Invalid Depot ID or Password")

    return render_template("depot_login.html")