import json
import os
import secrets

from apscheduler.schedulers.background import BackgroundScheduler
from config import (get_db, close_db, fetch_buy_pages, generate_thumbnail,
add_product, get_all_products, get_products_by_section, get_product_by_id, update_product_status,
delete_product, add_raffle, get_all_raffles, get_raffle_by_id, update_raffle_status, end_raffle, 
get_username, get_password, verify_login, update_gold_price, close_connection)
from flask import Flask, flash, jsonify, render_template, redirect, request, session, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.add_job(update_gold_price, 'interval', hours=1)
scheduler.start()

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

app.config.update(config)

authenticated = False

app.secret_key = secrets.token_hex(16)

upload_folder = os.path.join(os.getcwd(), config['UPLOAD_FOLDER'])
thumbnail_folder = os.path.join(os.getcwd(), config['THUMBNAIL_FOLDER'])
    
def create_directories():
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    if not os.path.exists(thumbnail_folder):
        os.makedirs(thumbnail_folder)

create_directories()

def is_staff():
    if 'username' in session:
        username = session['username']
        user = get_username(username)
        return user['staff']
    return False

@app.route('/', methods=["GET", "POST"])
def homepage():
    return render_template("index.html")

@app.route("/raffles", methods=["GET", "POST"])
def display_raffles():
    raffles = get_all_raffles()
    return render_template("raffles.html", raffles = raffles)

@app.route('/display_raffles/<int:raffle_id>', methods=["GET", "POST"])
def rafflepage(raffle_id):
    page = get_raffle_by_id(raffle_id)
    return render_template('display_raffles.html', page=page)

@app.route("/chains", methods=["GET", "POST"])
def chains():
    chain_products = get_products_by_section('Chain')
    sale_prices = [max(product['price'], product['current_gold_price']) for product in chain_products]

    return render_template("chains.html", chain_products=chain_products, sale_prices=sale_prices)

@app.route("/bracelets", methods=["GET", "POST"])
def bracelets():
    bracelet_products = get_products_by_section('Bracelet')
    sale_prices = [max(product['price'], product['current_gold_price']) for product in bracelet_products]
    
    return render_template("bracelets.html", bracelet_products=bracelet_products, sale_prices=sale_prices)

@app.route("/bars", methods=["GET", "POST"])
def bars():
    bar_products = get_products_by_section('Gold')
    sale_prices = [max(product['price'], product['current_gold_price']) for product in bar_products]
    return render_template("bars.html", bar_products=bar_products, sale_prices=sale_prices)

@app.route("/creole", methods=["GET", "POST"])
def creole():
    creole_products = get_products_by_section('Creole')
    sale_prices = [max(product['price'], product['current_gold_price']) for product in creole_products]
    return render_template("creole.html", creole_products=creole_products, sale_prices=sale_prices)

@app.route("/studs", methods=["GET", "POST"])
def studs():
    stud_products = get_products_by_section('Studs')
    sale_prices = [max(product['price'], product['current_gold_price']) for product in stud_products]
    return render_template("studs.html", stud_products=stud_products, sale_prices=sale_prices)

@app.route("/watches", methods=["GET", "POST"])
def watches():
    watch_products = get_products_by_section('Watch')
    sale_prices = [max(product['price'], product['current_gold_price']) for product in watch_products]
    return render_template("watches.html", watch_products=watch_products, sale_prices=sale_prices)

@app.route("/rings", methods=["GET", "POST"])
def rings():
    ring_products = get_products_by_section('Ring')
    sale_prices = [max(product['price'], product['current_gold_price']) for product in ring_products]
    return render_template("rings.html", ring_products=ring_products, sale_prices=sale_prices)

@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product(product_id):
    product = get_product_by_id(product_id)
    sale_prices = max(product['price'], product['current_gold_price'])
    return render_template("product.html", product=product, sale_prices=sale_prices)

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

@app.route("/cart", methods=["GET", "POST"])
def cart():
    cart_ids = session.get('cart_ids', [])
    cart_raffle_ids = session.get('cart_raffle_ids', [])
    
    cart_products = []
    cart_raffles = []
    total_price = 0

    for product_id in cart_ids:
        product = get_product_by_id(product_id)
        
        if product and product['status'] == 'Available':
            item_total_price = max(product['price'], product['current_gold_price'])
            total_price += item_total_price

            cart_products.append({
                'item': product,
                'total_price': item_total_price
            })

    for raffle_id in cart_raffle_ids:
        raffle = get_raffle_by_id(raffle_id)

        if raffle and raffle['status'] == 'Slots Available':
            item_total_price = raffle['ticket']
            total_price += item_total_price

            cart_raffles.append({
                'item': raffle,
                'total_price': item_total_price
            })

    return render_template("cart.html", cart_products=cart_products, cart_raffles=cart_raffles, total_price=total_price)

@app.route('/add_to_bag/<int:item_id>', methods=["POST"])
def add_to_bag(item_id):
    product = get_product_by_id(item_id)
    raffle = get_raffle_by_id(item_id)

    if product is not None and product['status'] == 'Available':
        cart_ids = session.get('cart_ids', [])

        if item_id not in cart_ids:
            cart_ids.append(item_id)
            session['cart_ids'] = cart_ids
            flash('Product added to bag!', 'success')
        else:
            flash('Product is already in the bag.', 'info')
        return redirect(url_for('product', product_id=item_id))

    elif raffle is not None and raffle['status'] == 'Slots Available':
        cart_raffle_ids = session.get('cart_raffle_ids', [])

        if item_id not in cart_raffle_ids:
            cart_raffle_ids.append(item_id)
            session['cart_raffle_ids'] = cart_raffle_ids
            flash('Raffle ticket added to bag!', 'success')
        else:
            flash('Raffle ticket is already in the bag.', 'info')
        return redirect(url_for('display_raffles', raffle_id=item_id))

    else:
        flash('Item is currently unavailable - if you really love it, use contact to inquire.', 'error')
        return render_template("404.html"), 404


@app.route('/remove_from_bag/<int:item_id>', methods=["POST"])
def remove_from_bag(item_id):
    product = get_product_by_id(item_id)
    raffle = get_raffle_by_id(item_id)

    if product is not None:
        cart_ids = session.get('cart_ids', [])

        if item_id in cart_ids:
            cart_ids.remove(item_id)
            session['cart_ids'] = cart_ids
            flash('Product removed from bag!', 'success')
        else:
            flash('Product not found in the bag.', 'info')
        return redirect(url_for('cart'))

    elif raffle is not None:
        cart_raffle_ids = session.get('cart_raffle_ids', [])

        if item_id in cart_raffle_ids:
            cart_raffle_ids.remove(item_id)
            session['cart_raffle_ids'] = cart_raffle_ids
            flash('Raffle ticket removed from bag!', 'success')
        else:
            flash('Raffle ticket not found in the bag.', 'info')
        return redirect(url_for('cart'))

    else:
        flash('Item not found in the bag.', 'error')

@app.route('/checkout')
def checkout():
    pass

@app.route('/portal', methods=["GET", "POST"])
def portal():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if verify_login(username, password):
            session['username'] = username
            flash('Login Successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('portal'))

    return render_template("portal.html")

@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    if is_staff():
        return render_template("dashboard.html")
    else:
        return redirect(url_for('portal'))

@app.route("/addproduct", methods=["GET", "POST"])
def addproduct():   
    if is_staff():
        buy_pages = fetch_buy_pages()

        if request.method == "POST":
            section = request.form.get("section")
            name = request.form.get("item")
            brand = request.form.get("brand")
            sale_choice = request.form.get("sell_by_weight")
            weight = request.form.get("weight")
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

                add_product(section, name, brand, sale_choice, weight, price, description, image_filename,
                            f'thumbnail_{image_filename}')
                
                update_gold_price()
                return redirect(url_for('addproduct'))
            else:
                add_product(section, name, brand, sale_choice, weight, price, description, placeholder, placeholder)

                update_gold_price()
                return redirect(url_for('addproduct'))
            
        return render_template("addproduct.html", buy_pages=buy_pages)
    
    else:
        return redirect(url_for('portal'))
    
@app.route('/viewstock', methods=["GET", "POST"])
def viewstock():
    if is_staff():
    
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
    else:
        return redirect(url_for('portal'))

@app.route('/startraffle', methods=["GET", "POST"])
def startraffle():

    if is_staff():
        if request.method == "POST":
            raffle_data = {
                "item": request.form.get("item"),
                "brand": request.form.get("brand"),
                "weight": request.form.get("weight"),
                "slots": request.form.get("slots"),
                "ticket": request.form.get("ticket"),
                "description": request.form.get("description"),
                "pic_name": secure_filename(request.files.get("image").filename) if request.files.get("image") else "static/logo.png",
                "thumbnail_filename": f'thumbnail_{secure_filename(request.files.get("image").filename)}' if request.files.get("image") else "thumbnail_static/logo.png",
                "status": "Slots Available",
                "question": request.form.get("trivia"),
                "answer1": request.form.get("answer1"),
                "answer2": request.form.get("answer2"),
                "answer3": request.form.get("answer3"),
                "correct": request.form.get("correct")
            } 
            add_raffle(**raffle_data) 

        return render_template('startraffle.html')
    
    else:
        return redirect('portal')

@app.route('/editraffle', methods=["GET", "POST"])
def editraffle():
    if is_staff():
    
        raffle = get_all_raffles()

        if request.method == "POST":
            raffle_id = int(request.form.get('raffle_id'))
            action = request.form.get('action')

            for raffle_item in raffle:
                if raffle_item['id'] == raffle_id:
                    if action == 'Limited Slots':
                        update_raffle_status(raffle_id, 'Limited Slots')
                    elif action == 'Full':
                        update_raffle_status(raffle_id, 'Full')
                    elif action == 'Slots Available':
                        update_raffle_status(raffle_id, 'Slots Available')
                    elif action == 'Finish':
                        end_raffle(raffle_id)
                    break

        return render_template('editraffle.html', raffles=raffle)
    
    else:
        return redirect(url_for('portal'))

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

if __name__ == '__main__':
    app.run(debug=True)
