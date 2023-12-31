"""Account creation view."""

import os
import uuid
import hashlib
import pathlib
import flask
import muscle
import re
from .. import utils

@muscle.app.route('/accounts/login/')
def show_login():
    """Show the login page for a user."""

    if utils.check_logname_exists():
        return flask.redirect("/",302)
    

    return flask.render_template("login.html")

@muscle.app.route('/accounts/logout/')
def complete_logout():
    """Show the login page for a user."""

    return utils.clear_cookie()

@muscle.app.route('/accounts/create/')
def show_create():
    """Show the account creation page."""

    if utils.check_logname_exists():
        return flask.redirect("/",302)

    return flask.render_template("create.html")

@muscle.app.route('/accounts/edit/')
def show_edit():
    """Shows edit password."""

    if not utils.check_logname_exists():
        return flask.redirect("/accounts/login/", 302)

    return flask.render_template("edit.html")

@muscle.app.route('/accounts/more_info/')
def show_more_info():
    """Ask more questions to the user."""

    background_check = utils.do_background_check()
    if background_check:
        return background_check
    
    logname = flask.request.cookies.get('username')
    context = {"logname": logname}
    return flask.render_template("more_info.html", **context)

@muscle.app.route('/accounts/edit_more_info/')
def show_edit_more_info():
    """Edit more questions to the user."""

    background_check = utils.do_background_check()
    if background_check:
        return background_check
    
    logname = flask.request.cookies.get('username')
    context = {"logname": logname}
    return flask.render_template("edit_more_info.html", **context)
    

@muscle.app.route('/accounts/auth/')
def auth():
    """Authenticate a user."""

    if not utils.check_logname_exists():
        flask.abort(403)
    return flask.make_response("", 200)

@muscle.app.route('/accounts/', methods = ['POST'])
def handle_submit():
    """Handle submit info."""
    connection = muscle.model.get_db()
    print("Connection is ", connection)

    form = flask.request.form.to_dict()
    operation = form['operation']

    if operation == "login":
        return login_help(connection, form)
    if operation == "create":
        return create_help(connection, form)
    if operation == "edit":
        return edit_help(connection, form)
    if operation == "more":
        return more_help(connection, form)
    if operation == "edit_more":
        return edit_more_help(connection,form)
    return None
    
def login_help(connection, form):
    """Login help function."""

    username = form['username']
    password = form['password']

    # hash and salt according to user password
    user = check_user_exists(connection, username, password)
    if not user:
        error = "Username and/or password is incorrect. Please enter a valid username/password"
        return flask.render_template("login.html", error=error)
    
    password_db_string = get_hashed_password(password, user["password"])

    if password_db_string != user["password"]:
        error = "Username and/or password is incorrect. Please enter a valid username/password"
        return flask.render_template("login.html", error=error)

    resp = flask.make_response(flask.redirect("/", 302))
    resp.set_cookie('username', username)
    return resp
        


def create_help(connection, form):
    """Account creation submit form."""

    name = form["fullname"]
    username = form['username']
    password = form['password']

    # check if account exits
    cur = connection.execute(
        "SELECT username, password "
        "FROM users "
        "WHERE username == ?",
        (username, )
    )

    user = cur.fetchall()

    if user:
        error = "Username already exists. Please enter a new username."
        return flask.render_template('create.html', error=error)

    password_regex = re.compile(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}')

    if not password_regex.match(password):
        error = 'Password must contain at least one number, one uppercase and lowercase letter, and at least 8 or more characters'
        return flask.render_template('create.html', error=error)

    hashed_password = hash_password(password)
    
    cur = connection.execute(
        "INSERT INTO users(username, password, age) "
        "VALUES (?, ?, ?)",
        (username, hashed_password,-1)
    )
    
    connection.commit()

    resp = flask.make_response(flask.redirect("/", 302))
    resp.set_cookie('username', username)
    return resp

def edit_help(connection, form):
    """Help with editing password."""

    if not utils.check_logname_exists():
        flask.abort(403)
    
    login_name = flask.request.cookies.get('username')
    password = form['password']
    new_password = form['new']
    new_password2 = form['new2']

    if new_password == "" or new_password2 == "":
        error = "New password is invalid. Please enter a valid password."
        return flask.render_template("edit.html", error = error)

    if new_password != new_password2:
        error = "Passwords do not match."
        return flask.render_template("edit.html", error = error)
    
    password_regex = re.compile(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}')

    if not password_regex.match(new_password):
        error = 'Password must contain at least one number, one uppercase and lowercase letter, and at least 8 or more characters'
        return flask.render_template('edit.html', error=error)

    user = check_user_exists(connection,login_name, password)
    password_db_string = get_hashed_password(password, user['password'])

    if not user:
        return flask.abort(403)

    if password_db_string == user['password']:
        new_password = hash_password(new_password)
        edit_password(connection,login_name,new_password)
        return flask.redirect("/",302)
    
    error = "Incorrect password. Please try again."
    return flask.render_template("edit.html", error = error)

def more_help(connection, form):
    """Adds new data to the existing user."""
    
    if not utils.check_logname_exists():
        return flask.redirect("/accounts/login/", 302)
    
    age = form['age']
    height = form['height']
    weight = form['weight']
    activity_level = form['activity_level']
    experience = form['experience']
    gender = form['gender']
    logname = flask.request.cookies.get('username')

    cur = connection.execute(
        "UPDATE users "
        "SET age = ?, height = ?, weight= ?, fitness_level = ?, workout_experience = ?, gender = ? "
        "WHERE username = ? ",
        (age, height, weight, activity_level, experience, gender, logname)
    )
    connection.commit()

    return flask.redirect("/", 302)

def edit_more_help(connection,form):
    """Edit users information form."""
    
    if not utils.check_logname_exists():
        return flask.redirect("/accounts/login/", 302)
    
    age = form['age']
    height = form['height']
    weight = form['weight']
    activity_level = form['activity_level']
    experience = form['experience']
    gender = form['gender']
    logname = flask.request.cookies.get('username')

    cur = connection.execute(
        "UPDATE users "
        "SET age = ?, height = ?, weight= ?, fitness_level = ?, workout_experience = ?, gender = ? "
        "WHERE username = ? ",
        (age, height, weight, activity_level, experience, gender, logname)
    )
    connection.commit()

    return flask.redirect("/", 302)


def edit_password(connection, username, new_password):
    """Change the password."""

    cur = connection.execute(
        "UPDATE users "
        "SET password = ? "
        "WHERE username == ? ",
        (new_password, username,)
    )

    connection.commit()
    

def hash_password(password):
    """Hash a password."""

    # hash and salt
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_db_string = salt + password
    hash_obj.update(password_db_string.encode('utf-8'))
    password_db_string = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_db_string])
    return password_db_string

def get_hashed_password(password, db_password):
    """Hashes user input according to db salt."""

    algorithm = 'sha512'
    salt = db_password.split("$")
    salt = salt[1]
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string

def check_user_exists(connection, username, password):
    """Check if a user exists."""

    if username == "" or password == "":
        flask.abort(400)

    cur = connection.execute(
        "SELECT username, password "
        "FROM users "
        "WHERE username == ?",
        (username,)
    )
    user = cur.fetchone()
    return user