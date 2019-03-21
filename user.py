from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, jsonify, redirect, render_template, request, session, send_file
from application import db

app = Flask(__name__)

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

