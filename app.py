import os
import secrets

from flask import Flask, flash, render_template, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

hashed_password = generate_password_hash(Config.PASSWORD)

authenticated = False

app.secret_key = secrets.token_hex(16)

@app.route('/', methods=["GET", "POST"])
def homepage():
    return render_template("index.html")

@app.route("/raffles", methods=["GET", "POST"])
def raffles():
    return render_template("raffles.html")

@app.route("/chains", methods=["GET", "POST"])
def chains():
    return render_template("chains.html")

@app.route("/bracelets", methods=["GET", "POST"])
def bracelets():
    return render_template("bracelets.html")

@app.route("/bars", methods=["GET", "POST"])
def bars():
    return render_template("bars.html")

@app.route("/creole", methods=["GET", "POST"])
def creole():
    return render_template("creole.html")

@app.route("/studs", methods=["GET", "POST"])
def studs():
    return render_template("studs.html")

@app.route("/watches", methods=["GET", "POST"])
def watches():
    return render_template("watches.html")

@app.route("/rings", methods=["GET", "POST"])
def rings():
    return render_template("rings.html")

@app.route("/sellgold", methods=["GET", "POST"])
def sellgold():
    return render_template("sellgold.html")

@app.route("/selljewellery", methods=["GET", "POST"])
def selljewellery():
    return render_template("selljewellery.html")

@app.route("/consign", methods=["GET", "POST"])
def consign():
    return render_template("consign.html")

@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    return render_template("contact.html")

@app.route('/portal', methods=["GET", "POST"])
def portal():
    global authenticated
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        stored_hashed_password = hashed_password

        if username == Config.USERNAME and check_password_hash(stored_hashed_password, password):
            
            authenticated = True
            flash('Login Successful', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template("portal.html")

@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    global authenticated
    if not authenticated:
        return redirect("/portal")
    
    return render_template("dashboard.html")

def fetch_buy_pages():
    return ["Chain", "Bracelet", "Gold", "Creole", "Studs", "Watch", "Ring"]

@app.route("/addproduct", methods=["GET", "POST"])
def addprodcut():
    global authenticated
    if not authenticated:
        return redirect("/portal")
    
    buy_pages = fetch_buy_pages()
    return render_template("addproduct.html", buy_pages=buy_pages)