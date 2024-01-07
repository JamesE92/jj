import json
import os
import secrets

from config import Config, get_db, close_db, fetch_buy_pages, generate_thumbnail, add_product, get_all_products, get_products_by_section, get_product_by_id, update_product_status, delete_product, close_connection
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

@app.route('/display_raffles/<int:raffle_id>', methods=["GET", "POST"])
def rafflepage(raffle_id):
    page = next((item for item in raffle if item['id'] == raffle_id), None)

    return render_template('display_raffles.html', page=page, raffle=raffle)


@app.route("/chains", methods=["GET", "POST"])
def chains():
    chain_products = get_products_by_section('Chain')
    return render_template("chains.html", chain_products=chain_products)

@app.route("/bracelets", methods=["GET", "POST"])
def bracelets():
    bracelet_products = get_products_by_section('Bracelet')
    return render_template("bracelets.html", bracelet_products=bracelet_products)

@app.route("/bars", methods=["GET", "POST"])
def bars():
    bar_products = get_products_by_section('Gold')
    return render_template("bars.html", bar_products=bar_products)

@app.route("/creole", methods=["GET", "POST"])
def creole():
    creole_products = get_products_by_section('Creole')
    return render_template("creole.html", creole_products=creole_products)

@app.route("/studs", methods=["GET", "POST"])
def studs():
    stud_products = get_products_by_section('Studs')
    return render_template("studs.html", stud_products=stud_products)

@app.route("/watches", methods=["GET", "POST"])
def watches():
    watch_products = get_products_by_section('Watch')
    return render_template("watches.html", watch_products=watch_products)

@app.route("/rings", methods=["GET", "POST"])
def rings():
    ring_products = get_products_by_section('Ring')
    return render_template("rings.html", ring_products=ring_products)

@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product(product_id):
    product = get_product_by_id(product_id)
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
        weight = float(request.form.get("weight"))
        price = float(request.form.get("price"))
        description = request.form.get("description")

        placeholder = '/static/logo.png'
        uploaded_image = request.files.get('image')
        image_filename = secure_filename(uploaded_image.filename) if uploaded_image else placeholder

        if uploaded_image:
            image_path = os.path.join(upload_folder, image_filename)
            uploaded_image.save(image_path)

            thumbnail = generate_thumbnail(image_path)
            thumbnail.save(os.path.join(thumbnail_folder, f'thumbnail_{image_filename}'))

            add_product(section, name, brand, weight, price, description, image_filename, f'thumbnail_{image_filename}')
        else:
            add_product(section, name, brand, weight, price, description, placeholder, placeholder)

    return render_template("addproduct.html", buy_pages=buy_pages)

@app.route('/viewstock', methods=["GET", "POST"])
def viewstock():
    global authenticated
    if not authenticated:
        return redirect("/portal")
    
    products = get_all_products()
    
    if request.method == "POST":
        product_id = int(request.form.get('product_id'))
        action = request.form.get('action')

        for product in products:
            if product['id'] == product_id:
                if action == 'reserved':
                    update_product_status(product_id, 'Reserved')
                elif action == 'available':
                    update_product_status(product_id, 'Available')
                elif action == 'sold':
                    delete_product(product_id)
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
            "ticket": ticket,
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

@app.route('/editraffle', methods=["GET", "POST"])
def editraffle():
    global authenticated
    if not authenticated:
        return redirect('/portal')
    
    if request.method == "POST":
        raffle_id = int(request.form.get('raffle_id'))
        action = request.form.get('action')

        for raffle_item in raffle:
            if raffle_item['id'] == raffle_id:
                if action == 'Limited Slots':
                    raffle_item['status'] = 'Limited Slots'
                elif action == 'Full':
                    raffle_item['status'] = 'Full'
                elif action == 'Slots Available':
                    raffle_item['status'] = 'Slots Available'
                elif action == 'Finish':
                    raffle.remove(raffle_item)
                break
    return render_template('editraffle.html', raffles=raffle)


@app.teardown_appcontext
def teardown_db(exception):
    close_db()

if __name__ == '__main__':
    app.run(debug=False)
