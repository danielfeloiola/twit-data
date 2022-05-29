import os

import tweepy
from flask import Flask, flash, jsonify, redirect, render_template, request, session, send_file
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Set up SQL Database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# adjust database url
uri = os.environ['DATABASE_URL']

#uri = os.getenv("DATABASE_URL")  # or other relevant config var
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
db = SQLAlchemy(app)

#set up secret key
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']


# makes a user class for the database
from user import User
from mappers import hashtag_map, trends_map, tweets_map, nuvem_de_palavras



@app.route("/")
#@login_required
def index():
    """Show the main page with instructions"""
    return render_template("index.html")


@app.route("/tweets", methods=["GET", "POST"])
@login_required
def tweets():
    """Show the map with the user tweets"""

    if request.method == "POST":
        usuario = request.form.get("usr_search")
        tweets_map(usuario)
        return render_template("tweets_map.html")
    else:
        return render_template("tweets.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    # check if username is available
    username = request.args.get('username')
    check_username = User.query.filter_by(username=username).first()

    # warns the user if it is - or not
    if not check_username:
        return jsonify(True)
    else:
        return jsonify(False)


@app.route("/trends", methods=["GET", "POST"])
@login_required
def trends():
    """Show map with local trending topics"""

    if request.method == "POST":

        place = request.form.get("selector")
        #tries to generate the map, warns the user if there is a err 88
        try:
            trends_map(place)
        except tweepy.TweepError as e:
            if e.response.text[51:-3] == '88':
                return apology("API Error 88")

        # if all go well generate the map
        return render_template("trends.html")

    else:
        return render_template("trends_form.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # query database to check if user exists
        user = User.query.filter_by(username=request.form.get("username")).first()
        password_check = user.check_password(request.form.get("password"))

        # if the passwords match, do the login
        if password_check == True:
            session["user_id"] = user.id
            session["username"] = user.username
            #session["user_id"] = user.username
        else:
            return apology("invalid username and/or password", 403)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/nuvem", methods=["GET", "POST"])
@login_required
def nuvem():
    """generate a wordcloud"""

    # User reached route via POST
    if request.method == "POST":
        usuario = request.form.get("usr_nv")
        frase, frase2, frase3, frase4, nuvem = nuvem_de_palavras(usuario)
        return render_template("nuvem_de_palavras.html",
                                frase = frase,
                                frase2 = frase2,
                                frase3 = frase3,
                                frase4 = frase4,
                                nuvem = nuvem)

    # if the user is looking for the form
    else:
        return render_template("nuvem.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

     # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

         # Ensure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match", 403)

        # check API consumer key
        if not request.form.get("consumer_key"):
            return apology("Check Consumer Key", 403)

        # check API consumer secret
        if not request.form.get("consumer_secret"):
            return apology("Check Consumer Secret", 403)

        # check API access token
        if not request.form.get("access_token"):
            return apology("Check Access Token", 403)

        # check API access secret
        if not request.form.get("access_secret"):
            return apology("Check Access Secret", 403)

        # encrypt passwprd
        hash_password = generate_password_hash(request.form.get("password"))

        # set username
        username = request.form.get("username")
        print(username)

        # get keys
        c_key = request.form.get("consumer_key")
        c_secret = request.form.get("consumer_secret")
        a_token = request.form.get("access_token")
        a_secret = request.form.get("access_secret")

        # query to check if the username already exists
        username_query = User.query.filter_by(username=request.form.get("username")).first()

        # if its a unique udername add user to database, if its not generate error
        if not username_query:
            new_user = User(username, hash_password, c_key, c_secret, a_token, a_secret)
            db.session.add(new_user)
            db.session.commit()
        else:
            return apology("username already exists", 403)

        # query database to check if user exists
        user = User.query.filter_by(username=request.form.get("username")).first()
        password_check = user.check_password(request.form.get("password"))

        # if the passwords match, do the login
        if password_check == True:
            session["user_id"] = user.id
            session["username"] = user.username
        else:
            return apology("invalid username and/or password", 403)

        # Redirect user to home page
        return redirect("/")

    # if the user is looking for the login page
    else:
        return render_template("register.html")


@app.route("/hashtags", methods=["GET", "POST"])
@login_required
def hashtags():
    """Show a map of places where a hashtag is being used"""

    # User reached route via POST
    if request.method == "POST":

        # Get the hashtag
        hashtag = request.form.get("hashtag")

        # Make a new map
        try:
            hashtag_map(hashtag)
        except tweepy.TweepError as e:
            # if there is a tweepy error
            return apology("Twitter Error", e.reason[-3:])

        return render_template("hashtag_map.html")

    # if the user is looking for the form
    else:
        return render_template("hashtag_form.html")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    """Change the users password"""

    if request.method == "POST":

        # Get the passwords
        current_password = request.form.get("current-password")
        new_password = request.form.get("new-password")
        new_password_check = request.form.get("new-password-check")

        # check if user has provided the password
        if not request.form.get("new-password"):
            return apology("must provide a new password", 403)

        # check if new passwords match
        if new_password != new_password_check:
            return apology("New passwords don't match", 403)

        # find the user in the database
        user = User.query.filter_by(id=session["user_id"]).first()
        check_pw = user.check_password(request.form.get("current-password"))

        # if the current password provided is correct
        if check_pw == True:

            # encrypt new pw
            user.hashp = generate_password_hash(request.form.get("new-password"))

            # add to database
            db.session.add(user)
            db.session.commit()

        return redirect("/")

    # if the user is looking for the form
    else:
        return render_template("changepassword.html")


@app.route("/changeapi", methods=["GET", "POST"])
@login_required
def changeapi():
    """Change the users api keys"""

    if request.method == "POST":

        # find the user in the database
        user = User.query.filter_by(id=session["user_id"]).first()

        # check if user has provided all the keys
        if not request.form.get("consumer_key"):
            return apology("Check Consumer Key", 403)

        # check API consumer secret
        if not request.form.get("consumer_secret"):
            return apology("Check Consumer Secret", 403)

        # check API access token
        if not request.form.get("access_token"):
            return apology("Check Access Token", 403)

        # check API access secret
        if not request.form.get("access_secret"):
            return apology("Check Access Secret", 403)

        # Get the new keys
        user.c_key = request.form.get("consumer_key")
        user.c_secret = request.form.get("consumer_secret")
        user.a_token = request.form.get("access_token")
        user.a_secret = request.form.get("access_secret")

        # add to database
        db.session.add(user)
        db.session.commit()

        return redirect("/")

    # if the user is looking for the form
    else:
        return render_template("changeapi.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


