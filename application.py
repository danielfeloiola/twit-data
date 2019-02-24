import os

#from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from helpers import apology, login_required
from helpers import tweet_map, mapa_hashtags, mapa_trends, hashtag_map, trends_map, tweets_map, nuvem_de_palavras



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


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
#db = SQL("postgres://tjgjscbrzpgexl:b2385bf5ba78252b0d910e8398f35d42a18db9578f5c254718598346bfea0815@ec2-54-227-246-152.compute-1.amazonaws.com:5432/d8na5t6e3e527i")

engine = "postgres://tjgjscbrzpgexl:b2385bf5ba78252b0d910e8398f35d42a18db9578f5c254718598346bfea0815@ec2-54-227-246-152.compute-1.amazonaws.com:5432/d8na5t6e3e527i"
db = scoped_session(sessionmaker(bind=engine))

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
        usuario = request.form.get("usuario")
        mapa = tweets_map(usuario)
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
    # NEEDS FIX: THE TRENDS LIST IS NOT THE SAME FROM THE TWITTER SITE.
    trends_map()
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

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        #makes the username global
        username = request.form.get("username")

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
        usuario = request.form.get("usuario")
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

        # check API login credentials
        if not request.form.get("consumer_key"):
            return apology("Check API credentials", 403)

        if not request.form.get("consumer_secret"):
            return apology("Check API credentials", 403)

        if not request.form.get("access_token"):
            return apology("Check API credentials", 403)

        if not request.form.get("access_secret"):
            return apology("Check API credentials", 403)

        # encrypt passwprd
        hash_password = generate_password_hash(request.form.get("password"))

        # get keys
        c_key = request.form.get("consumer_key")
        c_secret = request.form.get("consumer_secret")
        a_token = request.form.get("access_token")
        a_secret = request.form.get("access_secret")

        # try to add user to database
        result = db.execute("INSERT INTO users (username, hash, c_key, c_secret, a_token, a_secret) VALUES (:username, :hash_password, :c_key, :c_secret, :a_token, :a_secret)",
                          username = request.form.get("username"),
                          hash_password = hash_password,
                          c_key = c_key,
                          c_secret = c_secret,
                          a_token = a_token,
                          a_secret = a_secret)
        db.commit()

        if not result:
            return apology("username already exists", 403)

        # Do the login
        session["user_id"] = result
        print(session)

        # makes username global
        username = request.form.get("username")

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
        hashtag = request.form.get("hashtag")
        hashtag_map(hashtag)
        return render_template("hashtag_map.html")

    # if the user is looking for the form
    else:
        return render_template("hashtag_form.html")


# Render functions
@app.route("/mapatrends")
@login_required
def mapatrends():
    """Render map"""
    return mapa_trends.get_root().render()

@app.route("/tweets_map_renderer")
@login_required
def tweets_map_renderer():
    """Render map"""
    return tweet_map.get_root().render()

@app.route("/hastag_map_render")
@login_required
def hastag_map_render():
    """Render Map"""
    return mapa_hashtags.get_root().render()



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


