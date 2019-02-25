import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required
from helpers import tweet_map, mapa_hashtags, mapa_trends, hashtag_map, trends_map, tweets_map, nuvem_de_palavras


# Configure application
app = Flask(__name__)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hashp = db.Column(db.String(80), unique=True, nullable=False)
    c_key = db.Column(db.String(25), unique=True, nullable=False)
    c_secret = db.Column(db.String(50), unique=True, nullable=False)
    a_token = db.Column(db.String(50), unique=True, nullable=False)
    a_secret = db.Column(db.String(45), unique=True, nullable=False)


    def __init__(self, username, hashp, c_key, c_secret, a_token, a_secret):
        self.username = username
        self.hashp = hashp
        self.c_key = c_key
        self.c_secret = c_secret
        self.a_token = a_token
        self.a_secret = a_secret

    def check_password(self, password):
        return check_password_hash(self.hashp, password)



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
#app.config["SESSION_FILE_DIR"] = mkdtemp()
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"
#Session(app)


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


        usr = User.query.filter_by(username=request.form.get("username")).first()

        x = usr.check_password(request.form.get("password"))

        if x == True:
            # Remember which user has logged in
            session["user_id"] = usr.id
        elif x == False:
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

        # set username
        username = request.form.get("username")

        # get keys
        c_key = request.form.get("consumer_key")
        c_secret = request.form.get("consumer_secret")
        a_token = request.form.get("access_token")
        a_secret = request.form.get("access_secret")

        # try to add user to database
        new_user = User(username, hash_password, c_key, c_secret, a_token, a_secret)
        db.session.add(new_user)
        db.session.commit()

        usr = User.query.filter_by(username=request.form.get("username")).first()

        x = usr.check_password(request.form.get("password"))

        if x == True:
            # Remember which user has logged in
            session["user_id"] = usr.id
        else:
            return apology("username already exists", 403)

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


