import os
import secrets

from flask import Flask, flash, render_template, redirect, request, session

app = Flask(__name__)

app.secret_key = secrets.token_hex(16)

@app.route('/', methods=["GET", "POST"])
def homepage():
    return render_template("index.html")

@app.route('/portal', methods=["GET", "POST"])
def backstage():
    return render_template("portal.html")
