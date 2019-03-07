import os

import tweepy
from flask import Flask, flash, jsonify, redirect, render_template, request, session, send_file
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from usr import User
from helpers import apology, login_required
from mappers import hashtag_map, trends_map, tweets_map, nuvem_de_palavras


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
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

#set up secret key
app.config['SECRET_KEY'] = "shdulhdkj48fslu45jvkawinveohlf"


@app.route("/")
@login_required
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
    return jsonify("TODO")


@app.route("/trends")
@login_required
def trends():
    """Show map with local trending topics"""

    try:
        trends_map()
    except tweepy.TweepError:
        return apology("Twitter Error")

    return render_template("trends.html")


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
        usr = User.query.filter_by(username=request.form.get("username")).first()
        x = usr.check_password(request.form.get("password"))

        # if the passwords match, do the login
        if x == True:
            session["user_id"] = usr.id
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

        # Ensure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match", 403)

        # encrypt passwprd
        hash_password = generate_password_hash(request.form.get("password"))

        # set username
        username = request.form.get("username")

        # get keys
        c_key = request.form.get("consumer_key")
        c_secret = request.form.get("consumer_secret")
        a_token = request.form.get("access_token")
        a_secret = request.form.get("access_secret")

        # query to check if the username already exists
        usern = User.query.filter_by(username=request.form.get("username")).first()

        # if its a unique udername add user to database, if its not generate error
        if not usern:
            new_user = User(username, hash_password, c_key, c_secret, a_token, a_secret)
            db.session.add(new_user)
            db.session.commit()
        else:
            return apology("username already exists", 403)

        # query again for login
        usr = User.query.filter_by(username=request.form.get("username")).first()
        x = usr.check_password(request.form.get("password"))

        # do the login chacking for password
        if x == True:
            # Remember which user has logged in
            session["user_id"] = usr.id

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


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


#######
#app.config["SESSION_FILE_DIR"] = mkdtemp()
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"


#from tempfile import mkdtemp

#import requests
#import urllib.parse
#from tempfile import mkdtemp



#import branca
#import collections
#from operator import itemgetter
#from folium import IFrame
#from wordcloud import WordCloud
#import matplotlib.pyplot as plt
#import folium
#import re
#from functools import wraps

#from setup import list_capitais, list_coordenadas, list_woeids


# Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_FILE_DIR"] = mkdtemp()
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"
#app.config["SESSION_TYPE"] = "sqlalchemy"

#app.secret_key = "shdulhdkj48fslu45jvka7wfdnu126eohfsylf"
#Session(app)




# Creates a class for the sqlalchemy database

####################################################################################################################################



####################################################################################################################################




##################################
# PRECISA SER ARMAZENADO USANDO session['mapa_coisa']
#cria os mapas
#session['mp_tweet'] = folium.Map(location=[-12, -49], zoom_start=4)
#session['mp_hashtags'] = folium.Map(location=[-12, -49], zoom_start=4)
#session['mp_trends'] = folium.Map(location=[-12, -49], zoom_start=3)


# Render functions
#@app.route("/mapatrends")
#@login_required
#def mapatrends():
#    """Render map"""
#
#    return mp_trends.get_root().render()
#    # return session['mp_trends'].get_root().render()
#
#@app.route("/tweets_map_renderer")
#@login_required
#def tweets_map_renderer():
#    """Render map"""
#
#    return mp_tweet.get_root().render()
#    # return session['mp_tweet'].get_root().render()
#
#@app.route("/hastag_map_render")
#@login_required
#def hastag_map_render():
#    """Render Map"""
#
#    return mp_hashtags.get_root().render()
#    #return session['mp_hashtags'].get_root().render()
#
#
#, mp_tweet