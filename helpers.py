import requests
import urllib.parse
from flask import redirect, render_template, request, session, send_file
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


#import os

#import requests
#import urllib.parse
#from functools import wraps
#from flask import Flask, flash, jsonify, redirect, render_template, request, session, send_file
#from flask_session import Session
#from flask_sqlalchemy import SQLAlchemy
#from tempfile import mkdtemp
#from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
#from werkzeug.security import check_password_hash, generate_password_hash

