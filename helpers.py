import os

import requests
import urllib.parse
from functools import wrapsfrom flask import Flask, flash, jsonify, redirect, render_template, request, session, send_file
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from wordcloud import WordCloud
import matplotlib.pyplot as plt
import folium
import re
import tweepy


#cria os mapas
tweet_map = folium.Map(location=[-12, -49], zoom_start=4)
mapa_hashtags = folium.Map(location=[-12, -49], zoom_start=4)
mapa_trends = folium.Map(location=[-12, -49], zoom_start=3)


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
    tweets = tweepy.Cursor(api.search, q=hashtag, wait_on_rate_limit=True).items(1000)

    #listas de coordenadas e nomes de cidades
    lista_de_coordenadas = []

    #esse comentario e completamente inutil
    for tweet in tweets:

        if tweet.place != None:
            dados_lugar = tweet.place
            box = dados_lugar.bounding_box
            coordenadas = box.coordinates
            coords = coordenadas[0]
            coordenadas_agora_vai = coords[0]
            coordenadas_agora_vai.reverse()
            lista_de_coordenadas.append(coordenadas_agora_vai)

    #reitera pela lista de lugares e adiciona os marcadores
    numero = len(lista_de_coordenadas)
    for i in range(numero):
        folium.RegularPolygonMarker(lista_de_coordenadas[i],fill_color='#769d96',number_of_sides=8,radius=5).add_to(mapa_hashtags)


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
        folium.Marker(lista_de_coordenadas[i], popup=trends[i] + '<br>' + trends[i+1] +  '<br>' + trends[i+2]  +  '<br>' + trends[i+3] + '<br>' + trends[i+4] + '<br>' + trends[i+5] +  '<br>' + trends[i+6] + '<br>' + trends[i+7] + '<br>' + trends[i+8] + '<br>' + trends[i+9] + '<br>' + trends[i+10] + '<br>' + trends[i+11] + '<br>' + trends[i+12] + '<br>' + trends[i+13] + '<br>' + trends[i+14] + '<br>' + trends[i+15] + '<br>' + trends[i+16] + '<br>' + trends[i+17] + '<br>' + trends[i+18] + '<br>' + trends[i+19]).add_to(mapa_trends)


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


    stopwords =  open("stopwords-br.txt","r").read()

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

    return frase, frase2, frase3, frase4, nuvem

