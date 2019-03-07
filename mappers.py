# imports necessarios para criar os mapas
import matplotlib.pyplot as plt
import folium
import re
import tweepy
import branca
import requests

from wordcloud import WordCloud
from folium import IFrame
from operator import itemgetter

# importa configuracoes do app
from flask import Flask, flash, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

# importa definicoes de outros arquivos da mesma pasta
from cidades import list_capitais, list_coordenadas, list_woeids
from usr import User


# Salvar os mapas com a id do usuário no nome,
# depois carregar eles nas páginas que mostram os mapas
# que nem foi feito com a nuvem de palavras


#mp_tweet = folium.Map(location=[-12, -49], zoom_start=4)




def hashtag_map(hashtag):
    '''Faz um mapa mostrando onde hashtags foram usadas'''

    #pega a id do usuario
    id = session["user_id"]

    # Cria o mapa
    #session['mp_hashtags'] = folium.Map(location=[-12, -49], zoom_start=4)
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

    #listas de coordenadas e nomes de cidades
    #lista_de_coordenadas = []

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
            iframe = branca.element.IFrame(twt_html, width=300, height=400) # width=400, height=500

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
    #session['mp_tweet'] = folium.Map(location=[-12, -49], zoom_start=4)
    # Cria um mapa
    #session['mp_trends'] = folium.Map(location=[-12, -49], zoom_start=3)
    mp_trends = folium.Map(location=[-12, -49], zoom_start=3)

    # Pega a id do usuario
    id = session["user_id"]

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

        # Cria uma lista para armazenar os trends
        trends = []

        #pede os trends
        status_list = api.trends_place(list_woeids[i])

        #tira eles de dentro da primeira lista
        trending = status_list[0]

        #tira os trends de dentro de um dicionario
        trends_de_verdade = trending['trends']

        # calcula a quantidade de trends
        x = len(trends_de_verdade)

        # se houver dados de volume, coloca em uma tupla o trend e o volume
        for num in range(x):
            if trends_de_verdade[num]['tweet_volume'] is not None:
                # e coloca a tupla na lista
                trends.append((trends_de_verdade[num]['name'], trends_de_verdade[num]['tweet_volume']))

        # coloca os tts em ordem decrescente do tweet_volume
        trends = sorted(trends, key=itemgetter(1), reverse=True)

        # coloca os marcadores no mapa
        folium.Marker(list_coordenadas[i],popup= trends[0][0]+'  (' + str(trends[0][1])+' tweets)' + '<br>'
                                                    +trends[1][0]+'  (' + str(trends[1][1])+' tweets)' + '<br>'
                                                    +trends[2][0]+'  (' + str(trends[2][1])+' tweets)' + '<br>'
                                                    +trends[3][0]+'  (' + str(trends[3][1])+' tweets)' + '<br>'
                                                    +trends[4][0]+'  (' + str(trends[4][1])+' tweets)' + '<br>'
                                                    +trends[5][0]+'  (' + str(trends[5][1])+' tweets)' + '<br>'
                                                    +trends[6][0]+'  (' + str(trends[6][1])+' tweets)' + '<br>'
                                                    +trends[7][0]+'  (' + str(trends[7][1])+' tweets)').add_to(mp_trends)
                                                    #.add_to(session['mp_trends'])

    # Salva o mapa em um arquivo
    mp_trends.save(outfile = "static/mp_trends.html")

def tweets_map(usuario):
    ''' Mostra os tweets geolocalizados de um usuário em um mapa '''

    # Cria um mapa
    #session['mp_tweet'] = folium.Map(location=[-12, -49], zoom_start=4)
    mp_tweet = folium.Map(location=[-12, -49], zoom_start=4)

    # Pega a id do usuario
    id = session["user_id"]

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
            # Encontra o nome da cidade
            dados_lugar = status.place
            nome = dados_lugar.name
            lista_de_nomes.append(nome)
            # Encontra as coordenadas
            box = dados_lugar.bounding_box
            coordenadas = box.coordinates
            coords = coordenadas[0]
            coordenadas_finais = coords[0]
            coordenadas_finais.reverse()
            lista_de_coordenadas.append(coordenadas_finais)

    #Coleta dados de GPS embedados em um tweet
    for status in status_list:
        if status.coordinates != None:
            dados_lugar = status.coordinates
            coordenadas = dados_lugar['coordinates']
            coordenadas_finais = coordenadas
            coordenadas_finais.reverse()
            lista_de_coordenadas.append(coordenadas_finais)
            lista_de_nomes.append('Dados de GPS')

    # Se não houver dados de localização
    if not lista_de_coordenadas:
        print('Este usuario nao tem tweets com dados de geolocalizacao')

    # passa pela lista de lugares e adiciona os marcadores
    numero = len(lista_de_nomes)
    for i in range(numero):
        #folium.CircleMarker(lista_de_coordenadas[i], popup=lista_de_nomes[i]).add_to(session['mp_tweet'])#.add_to(mp_tweet)
        folium.Marker(lista_de_coordenadas[i], popup=lista_de_nomes[i]).add_to(mp_tweet)

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

