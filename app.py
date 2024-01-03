import json
import os
import secrets

from config import Config
from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

app.config.update(config)

app.config.from_object(Config)

hashed_password = generate_password_hash(Config.PASSWORD)

authenticated = False

app.secret_key = secrets.token_hex(16)

upload_folder = app.config['UPLOAD_FOLDER']
thumbnail_folder = app.config['THUMBNAIL_FOLDER']
    
def create_directories():
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    if not os.path.exists(thumbnail_folder):
        os.makedirs(thumbnail_folder)

create_directories()

products = []
product_id = 0

raffle = []
raffle_id = 0

@app.route('/', methods=["GET", "POST"])
def homepage():
    return render_template("index.html")

@app.route("/raffles", methods=["GET", "POST"])
def display_raffles():
    raffle_items = raffle
    return render_template("raffles.html", raffles=raffle_items)

@app.route('/rafflepage/<int:raffle_id>', methods=["GET", "POST"])
def rafflepage(raffle_id):
    page = raffle[raffle_id - 1]
    return render_template('display_raffles.html', page=page, raffle=raffle)


@app.route("/chains", methods=["GET", "POST"])
def chains():
    chain_products = [product for product in products if product['section'] == 'Chain']
    return render_template("chains.html", chain_products=chain_products)

@app.route("/bracelets", methods=["GET", "POST"])
def bracelets():
    bracelet_products = [product for product in products if product['section'] == 'Bracelet']
    return render_template("bracelets.html", bracelet_products=bracelet_products)

@app.route("/bars", methods=["GET", "POST"])
def bars():
    bar_products = [product for product in products if product['section'] == 'Gold']
    return render_template("bars.html", bar_products=bar_products)

@app.route("/creole", methods=["GET", "POST"])
def creole():
    creole_products = [product for product in products if product['section'] == 'Creole']
    return render_template("creole.html", creole_products=creole_products)

@app.route("/studs", methods=["GET", "POST"])
def studs():
    stud_products = [product for product in products if product['section'] == 'Studs']
    return render_template("studs.html", stud_products=stud_products)

@app.route("/watches", methods=["GET", "POST"])
def watches():
    watch_products = [product for product in products if product['section'] == 'Watch']
    return render_template("watches.html", watch_products=watch_products)

@app.route("/rings", methods=["GET", "POST"])
def rings():
    ring_products = [product for product in products if product['section'] == 'Ring']
    return render_template("rings.html", ring_products=ring_products)

@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product(product_id):
    product = products[product_id - 1]
    return render_template("product.html", product=product)

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

def generate_thumbnail(image_path):
    uploaded_image = Image.open(image_path)
    uploaded_image.thumbnail((150, 150))
    return uploaded_image

@app.route("/addproduct", methods=["GET", "POST"])
def addproduct():
    global product_id
    global authenticated
    if not authenticated:
        return redirect("/portal")    
    
    buy_pages = fetch_buy_pages()

    if request.method == "POST":
        section = request.form.get("section")
        name = request.form.get("item")
        brand = request.form.get("brand")
        weight = request.form.get("weight")
        price = request.form.get("price")
        description = request.form.get("description")

        placeholder = '/static/logo.png'
        uploaded_image = request.files.get('image')
        image_filename = secure_filename(uploaded_image.filename) if uploaded_image else placeholder

        if uploaded_image:
            image_path = os.path.join(upload_folder, image_filename)
            uploaded_image.save(image_path)
        else:
            image_path = os.path.join(upload_folder, placeholder)

        thumbnail = generate_thumbnail(image_path)
        thumbnail.save(os.path.join(thumbnail_folder, f'thumbnail_{image_filename}'))

        product_id += 1

        product_data = {
            "id": product_id,
            "section": section,
            "name":name,
            "brand": brand,
            "weight": weight,
            "price": price,
            "description": description,
            "image_filename": image_filename,
            "thumbnail_filename": f'thumbnail_{image_filename}',
            "status": "Available"
        }
        products.append(product_data)

    return render_template("addproduct.html", buy_pages=buy_pages)

@app.route('/viewstock', methods=["GET", "POST"])
def viewstock():
    global authenticated
    if not authenticated:
        return redirect("/portal")
    
    if request.method == "POST":
        product_id = int(request.form.get('product_id'))
        action = request.form.get('action')

        for product in products:
            if product['id'] == product_id:
                if action == 'reserved':
                    product['status'] = 'Reserved'
                elif action == 'available':
                    product['status'] = 'Available'
                elif action == 'sold':
                    products.remove(product)
                break

    return render_template('viewstock.html', products=products)

@app.route('/startraffle', methods=["GET", "POST"])
def startraffle():
    global authenticated
    if not authenticated:
        return redirect("/portal")

    global raffle_id
    if request.method == "POST":
        item = request.form.get("item")
        brand = request.form.get("brand")
        weight = request.form.get("weight")
        ticket = request.form.get("ticket")
        description = request.form.get("description")
        question = request.form.get("trivia")
        a1 = request.form.get("answer1")
        a2 = request.form.get("answer2")
        a3 = request.form.get("answer3")

        placeholder = "static/logo.png"
        picture = request.files.get("image")
        pic_name = secure_filename(picture.filename) if picture else placeholder

        if picture:
            pic_path = os.path.join(upload_folder, pic_name)
            picture.save(pic_path)
        else:
            pic_path = os.path.join(upload_folder, placeholder)

        thumbnail = generate_thumbnail(pic_path)
        thumbnail_filename = f'thumbnail_{pic_name}'
        thumbnail.save(os.path.join(thumbnail_folder, thumbnail_filename))

        raffle_id += 1

        raffle_data = {
            "id": raffle_id,
            "item": item,
            "brand": brand,
            "weight": weight,
            "price": ticket,
            "description": description,
            "pic_name": pic_name,
            "thumbnail_filename": thumbnail_filename,
            "question": question,
            "answer1": a1,
            "answer2": a2,
            "answer3": a3,
            "status": "Slots Available"
        }
        raffle.append(raffle_data)

    return render_template('startraffle.html')

@app.route('/endraffle', methods=["GET", "POST"])
def endraffle():
    return render_template('endraffle.html')
