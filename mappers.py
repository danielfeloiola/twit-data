# imports necessarios para criar os mapas###
import matplotlib.pyplot as plt
import folium
import re
import tweepy
import branca
import requests
from wordcloud import WordCloud
from folium import IFrame

# importa configuracoes do app
from flask import Flask, flash, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

# importa definicoes de outros arquivos da mesma pasta
from cidades import list_capitais, list_coordenadas, list_woeids
from user import User


def hashtag_map(hashtag):
    '''Faz um mapa mostrando onde hashtags foram usadas'''

    # Cria o mapa
    mp_hashtags = folium.Map(location=[-12, -49], zoom_start=4)

    # Cria uma api do twitter
    usr = User.query.filter_by(id=session["user_id"]).first()

    consumer_key = usr.c_key
    consumer_secret = usr.c_secret
    access_token = usr.a_token
    access_token_secret = usr.a_secret

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    # Call API to get the tweets
    tweets = tweepy.Cursor(api.search, q=hashtag).items(800) #, wait_on_rate_limit=True

    # esse comentario e completamente inutil
    for tweet in tweets:

        # Se eocontrarmos dados de geolocalizacao no tweet
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
            iframe = branca.element.IFrame(twt_html, width=280, height=320) # width=400, height=500

            # Make a folium popup
            popup = folium.Popup(iframe, parse_html=True, max_width=500)

            # Add marker to the map
            folium.Marker(coordenadas_agora_vai, popup = popup).add_to(mp_hashtags)
            #folium.Marker(coordenadas_agora_vai, popup = popup).add_to(session['mp_hashtags'])

    # Salva o mapa
    mp_hashtags.save(outfile = "static/mp_hashtags.html")


def trends_map():
    ''' Mostra trending topics locais '''

    # Cria um mapa
    mp_trends = folium.Map(location=[-12, -49], zoom_start=3)

    #cria uma api do twitter
    usr = User.query.filter_by(id=session["user_id"]).first()

    consumer_key = usr.c_key
    consumer_secret = usr.c_secret
    access_token = usr.a_token
    access_token_secret = usr.a_secret

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)


    # itera sobre as capitais pegando os trends de cada uma
    contador = len(list_capitais)

    for i in range(contador):

        trends = []

        # pede os trends
        status_list = api.trends_place(list_woeids[i])

        # tira eles de dentro de uma lista dentro de um dicionario
        trending = status_list[0]
        trends_de_verdade = trending['trends']

        # calcula a quantidade de trends
        x = len(trends_de_verdade)

        # Coloca os trends e o tweet_volume (se disponivel) na lista de trends
        for num in range(x):
            if trends_de_verdade[num]['tweet_volume'] is not None:
                trends.append((trends_de_verdade[num]['name'], trends_de_verdade[num]['tweet_volume']))
            else:
                trends.append((trends_de_verdade[num]['name'], 'No tweet_volume'))

        # Cria o HTML para o popoup do mapa

        html_list = []

        for j in range(45):
            html_list.append('<div style="font-family: sans-serif; font-size: 12px; line-height: 1.3em;">'
                             + trends[j][0] + '  (' + str(trends[j][1]) + ') ' + '</div>')

        html_popup = ''.join(html_list)

        iframe = branca.element.IFrame(html_popup, width=280, height=320) # width=400, height=500

        # cria o popup do folium
        popup = folium.Popup(iframe, parse_html=True)#, max_width=370

        # adiciona um marcador com o popup ao mapa
        folium.Marker(list_coordenadas[i], popup = popup).add_to(mp_trends) #add_to(m)

    # Salva o mapa em um arquivo
    mp_trends.save(outfile = "static/mp_trends.html")

def tweets_map(usuario):
    ''' Mostra os tweets geolocalizados de um usuário em um mapa '''

    # Cria um mapa
    mp_tweet = folium.Map(location=[-12, -49], zoom_start=4)

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

    # Coleta o dado de cidades embedado em um Tweet
    for status in status_list:
        if status.place != None:
            # Encontra os dados da cidade
            dados_lugar = status.place
            box = dados_lugar.bounding_box
            coordenadas = box.coordinates
            coords = coordenadas[0]
            coordenadas_finais = coords[0]
            coordenadas_finais.reverse()


    # Coleta dados de GPS embedados em um tweet
        if status.coordinates != None:
            dados_lugar = status.coordinates
            coordenadas = dados_lugar['coordinates']
            coordenadas_finais = coordenadas
            coordenadas_finais.reverse()

        # Se houverem dados de localizacao eles sao colocados no mapa
        if status.coordinates != None or status.place != None:

            # URL to get a embeddable version of the tweet
            url = 'https://publish.twitter.com/oembed?url=https://twitter.com/'+ status.user.screen_name +'/status/' + status.id_str

            # Get the embedable HTML out of the json
            twt_embed = requests.get(url)
            twt_json = twt_embed.json()
            twt_html = twt_json['html']

            # Add to the iframe
            iframe = branca.element.IFrame(twt_html, width=280, height=320) # width=400, height=500

            # Make a folium popup
            popup = folium.Popup(iframe, parse_html=True, max_width=500)

            # Add marker to the map
            folium.Marker(coordenadas_finais, popup=popup).add_to(mp_tweet)

    # Salva o mapa
    mp_tweet.save(outfile = "static/mp_tweets.html")

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

        #remove links de tweets
        tweetsemlink = re.sub(r"http\S+", "", str(tweet.text))
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

