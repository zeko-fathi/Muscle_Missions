"""Useful functions across all files."""

import flask
import muscle


def clear_cookie():
    """Clear a cookie if removed from database."""
    response = flask.make_response(flask.redirect('/accounts/login/'))  # Redirect or return a response
    response.set_cookie('username', '', expires=0)  # Clear the cookie
    return response
