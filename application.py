import os
import requests
import urllib.parse
import matplotlib.pyplot as plt
import folium
import re
import tweepy
import branca
from folium import IFrame
from wordcloud import WordCloud
from functools import wraps
from flask import Flask, flash, jsonify, redirect, render_template, request, session, send_file
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required


#cria os mapas
tweet_map = folium.Map(location=[-12, -49], zoom_start=4)
mapa_hashtags = folium.Map(location=[-12, -49], zoom_start=4)
mapa_trends = folium.Map(location=[-12, -49], zoom_start=3)


# Configure application
app = Flask(__name__)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

# Creates a class for the sqlalchemy database
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
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = "shdulhdkj48fslu45jvkawinveohlf"
Session(app)


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

    try:
        # tweepy function call
        trends_map()
    except tweepy.TweepError:
        return apology("Tweepy Error")

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
        hashtag = request.form.get("hashtag")

        try:
        # Some tweepy api call, ex) api.get_user(screen_name = usrScreenName)
            hashtag_map(hashtag)
        except tweepy.TweepError as e:
            #print(e.reason)
            return apology("Tweepy Error", e.reason[-3:])

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



####################################################
# funcoes que geram os mapas
def hashtag_map(hashtag):
    '''Faz um mapa mostrando onde hashtags foram usadas'''

    #cria uma api do twitter
    usr = User.query.filter_by(id=session["user_id"]).first()

    consumer_key = usr.c_key
    consumer_secret = usr.c_secret
    access_token = usr.a_token
    access_token_secret = usr.a_secret

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    # Call API to get the tweets
    tweets = tweepy.Cursor(api.search, q=hashtag).items(1000) #, wait_on_rate_limit=True

    #file = open("tweets.txt", "r")
    #tweets = file.read()

    #listas de coordenadas e nomes de cidades
    lista_de_coordenadas = []

    #esse comentario e completamente inutil
    for tweet in tweets:

        # Se eocontrarmos dadso de geolocalizacao no tweet
        if tweet.place != None:
            dados_lugar = tweet.place
            box = dados_lugar.bounding_box
            coordenadas = box.coordinates
            coords = coordenadas[0]
            coordenadas_agora_vai = coords[0]
            coordenadas_agora_vai.reverse()

            # URL to get a embeddable version of the tweet
            url = 'https://publish.twitter.com/oembed?url=https://twitter.com/'+ tweet.user.screen_name +'/status/' + tweet.id_str

            # Get the embedable HTML out of the json
            twt_embed = requests.get(url)
            twt_json = twt_embed.json()
            twt_html = twt_json['html']

            # Add to the iframe
            iframe = branca.element.IFrame(twt_html, width=300, height=400) # width=400, height=500

            # Make a folium popup
            popup = folium.Popup(iframe, parse_html=True, max_width=500)

            # Add marker to the map
            folium.Marker(coordenadas_agora_vai, popup = popup).add_to(mapa_hashtags)


def trends_map():
    ''' Mostra trending topics locais '''

    #cria uma api do twitter
    usr = User.query.filter_by(id=session["user_id"]).first()

    consumer_key = usr.c_key
    consumer_secret = usr.c_secret
    access_token = usr.a_token
    access_token_secret = usr.a_secret

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    # nomes das cidades, coordenadas e woeids
    lista_de_capitais = ['Manaus',
                         'Salvador',
                         'Fortaleza',
                         'Brasília',
                         'Goiânia',
                         'São Luís',
                         'Belo Horizonte',
                         'Belém',
                         'Curitiba',
                         'Recife',
                         'Rio de Janeiro',
                         'Porto Alegre',
                         'São Paulo']

    lista_de_coordenadas = [[ -3.07, -61.66],
                            [-12.96, -38.51],
                            [ -3.71, -38.54],
                            [-15.83, -47.86],
                            [-16.64, -49.31],
                            [ -2.55, -44.30],
                            [-18.10, -44.38],
                            [ -5.53, -52.29],
                            [-24.89, -51.55],
                            [ -8.28, -35.07],
                            [-22.84, -43.15],
                            [-30.01, -51.22],
                            [-23.55, -46.64]]

    lista_de_woeids = [
                       455833,
                       455826,
                       455830,
                       455819,
                       455831,
                       455834,
                       455821,
                       455820,
                       455822,
                       455824,
                       455825,
                       455823,
                       455827]

    # itera sobre as capitais pegando os trends de cada uma
    contador = len(lista_de_capitais)

    for i in range(contador):

        trends = []

        #pede os trends
        status_list = api.trends_place(lista_de_woeids[i])

        #pegas os trends e coloca na lista
        trending = status_list[0]
        trends_de_verdade = trending['trends']
        x = len(trends_de_verdade)
        for num in range(x):
            trends.append(trends_de_verdade[num]['name'])

        #coloca os marcadores no mapa
        folium.Marker(lista_de_coordenadas[i],
        popup = trends[i] + '<br>' + trends[i+1] +  '<br>' + trends[i+2]  +  '<br>'
        + trends[i+3] + '<br>' + trends[i+4] + '<br>' + trends[i+5] +  '<br>'
        + trends[i+6] + '<br>' + trends[i+7] + '<br>' + trends[i+8] + '<br>'
        + trends[i+9] + '<br>' + trends[i+10] + '<br>' + trends[i+11] + '<br>'
        + trends[i+12] + '<br>' + trends[i+13] + '<br>' + trends[i+14] + '<br>'
        + trends[i+15] + '<br>' + trends[i+16] + '<br>' + trends[i+17] + '<br>'
        + trends[i+18] + '<br>' + trends[i+19]).add_to(mapa_trends)


def tweets_map(usuario):
    ''' Mostra os tweets geolocalizados de um usuário em um mapa '''

    #cria uma api do twitter
    usr = User.query.filter_by(id=session["user_id"]).first()

    consumer_key = usr.c_key
    consumer_secret = usr.c_secret
    access_token = usr.a_token
    access_token_secret = usr.a_secret

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)


    # Busca a timeline do usuario
    status_list = api.user_timeline(usuario, count=3200, include_rts=False)

    #listas de coordenadas e nomes de cidades
    lista_de_coordenadas = []
    lista_de_nomes = []

    #Coleta o dado de cidades embedado em um Tweet
    for status in status_list:
        if status.place != None:
            dados_lugar = status.place

            nome = dados_lugar.name
            lista_de_nomes.append(nome)
            box = dados_lugar.bounding_box
            coordenadas = box.coordinates
            coords = coordenadas[0]
            coordenadas_agora_vai = coords[0]
            coordenadas_agora_vai.reverse()
            #print(coordenadas_agora_vai)
            lista_de_coordenadas.append(coordenadas_agora_vai)

    #Coleta dados de GPS embedados em um tweet
    for status in status_list:
        if status.coordinates != None:
            dados_lugar = status.coordinates
            coordenadas = dados_lugar['coordinates']
            coordenadas_agora_vai = coordenadas
            coordenadas_agora_vai.reverse()
            lista_de_coordenadas.append(coordenadas_agora_vai)
            lista_de_nomes.append('Dados de GPS')

    # Se não houver dados de localização
    if not lista_de_coordenadas:
        print('Este usuario nao tem tweets com dados de geolocalizacao')

    #reitera pela lista de lugares e adiciona os marcadores
    numero = len(lista_de_nomes)
    for i in range(numero):
        folium.Marker(lista_de_coordenadas[i], popup=lista_de_nomes[i]).add_to(tweet_map)


def nuvem_de_palavras(usuario):
    '''Mostra alguns dados de um perfil do twitter e faz uma nuvem de palavras'''

    #cria uma api do twitter
    usr = User.query.filter_by(id=session["user_id"]).first()

    consumer_key = usr.c_key
    consumer_secret = usr.c_secret
    access_token = usr.a_token
    access_token_secret = usr.a_secret

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    # le as stopwords de um arquivo no diretorio
    stopwords =  open("stopwords-br.txt","r").read()

    # cria uma string vazia para adicionar os tweets
    string = ''

    # pega a timeline de um usuário
    timeline = api.user_timeline(usuario, count=2200, include_rts=False)

    # coloca os tweets na lista
    for tweet in timeline:
        tweetsemlink = re.sub(r"http\S+", "", str(tweet.text))#remove links de tweets
        string += str(tweetsemlink)

    # transforma uma str com vários tweets em lista de palavras
    wordList = re.sub("[^\w]", " ",  string).split()

    # remove as stopwords e coloca numa lista
    lista_filtrada = wordList[:] #make a copy of the word_list
    for palavra in wordList: # iterate over word_list
        if palavra.lower() in stopwords: #verifica as palavras usando caixa baixa
            lista_filtrada.remove(palavra) # remove word from filtered_word_list if it is

    # junta tudo em uma string para montar uma lista de palavras
    string_final = ' '.join(lista_filtrada)

    # faz a nuvem de palavras
    wordcloud = WordCloud(max_font_size=32, background_color="white").generate(string_final)
    plt.figure(figsize=[12,12])
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()

    wordcloud.to_file("static/nuvem.png")
    nuvem = "static/nuvem.png"

    # info_do_perfil do usuario:
    consulta_api = api.get_user(usuario)._json
    nome = consulta_api['name']
    descricao = consulta_api['description']
    seguidores = consulta_api['followers_count']
    site = consulta_api['url']

    # cria as frases que serão exibidas
    frase = f'O usuário {usuario} tem {seguidores} seguidores no Twitter'
    frase2 = f'O nome oficial do {usuario} é: {nome}'
    frase3 = f'A descrição do {usuario} é: {descricao}'
    frase4 = f'O site do {usuario} é: {site}'

    # the end
    return frase, frase2, frase3, frase4, nuvem

