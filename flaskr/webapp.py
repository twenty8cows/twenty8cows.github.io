import logging
import os
from datetime import datetime
from io import BytesIO

import bcrypt
import psycopg
import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    render_template,
    request,
    jsonify,
    send_file,
    abort,
    url_for,
    flash,
    redirect,
)
from flask_mail import Mail,Message
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

today = datetime.today().date()

app = Flask(__name__)
mail = Mail(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['SECRET_KEY'] = os.getenv('SECRET_EMAIL_KEY')

mail = Mail(app)



# Security Headers
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self' 'unsafe-inline';"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

def db_connection():
    """Establishes connection for queries"""
    conn = None
    try:
        conn = psycopg.connect(
            dbname=os.getenv("dbname"),
            user=os.getenv("user"),
            host=os.getenv("host"),
            password=os.getenv("password"),
            row_factory=dict_row,
        )
    except Exception as err:
        logging.error(f"Database connection error: {err}")
    return conn

def get_partitioned_table_name(date):
    """Generates the partitioned table name based on the date."""
    return f"dispo_prices_{date.strftime('%Y_%m')}"

def get_distinct_categories(column_name: str, date):
    """Fetches distinct category"""
    table_name = get_partitioned_table_name(date)
    conn = db_connection()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            query = SQL("SELECT DISTINCT {} FROM {} WHERE date = %s ORDER BY {} ASC").format(
                Identifier(column_name), Identifier(table_name), Identifier(column_name)
            )
            cur.execute(query, [date])
            values = cur.fetchall()
            return [value[column_name] for value in values]
    except Exception as err:
        logging.error(f"Error fetching distinct categories: {err}")
        return []
    finally:
        conn.close()

def get_distinct_values(column_name: str, date):
    """Fetch distinct values from the specified column in the partitioned table."""
    table_name = get_partitioned_table_name(date)
    conn = db_connection()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            query = SQL("SELECT DISTINCT {} FROM {} ORDER BY {}").format(
                Identifier(column_name), Identifier(table_name), Identifier(column_name)
            )
            cur.execute(query)
            values = cur.fetchall()
            return [value[column_name] for value in values]
    except Exception as err:
        logging.error(f"Error fetching distinct values: {err}")
        return []
    finally:
        conn.close()

def get_store_names(dispensary_name: str, date):
    """Fetch distinct store names for a given dispensary from the partitioned table."""
    if not dispensary_name:
        logging.warning("Dispensary name not provided.")
        return []

    table_name = get_partitioned_table_name(date)
    conn = db_connection()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            query = SQL(
                "SELECT DISTINCT store_name FROM {} WHERE dispensary_name = %s ORDER BY store_name"
            ).format(Identifier(table_name))
            cur.execute(query, (dispensary_name,))
            store_names = cur.fetchall()
            return [name["store_name"] for name in store_names]
    except Exception as err:
        logging.error(f"Error fetching store names: {err}")
        return []
    finally:
        conn.close()

@app.route("/")
def index() -> str:
    """Render the index page with distinct dispensaries and product categories."""
    dispensaries = get_distinct_values(column_name="dispensary_name", date=today)
    categories = get_distinct_categories(column_name="product_category", date=today)
    return render_template(
        template_name_or_list="index.html",
        dispensaries=dispensaries,
        categories=categories,
    )

@app.route("/fetch-image")
def fetch_image():
    image_urls = request.args.get("url")
    if not image_urls:
        return abort(400, "Image URL not provided")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:129.0) Gecko/20100101 Firefox/129.0",
        "Accept": "image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5",
        "Referer": "https://www.iheartjane.com/",
    }

    urls = image_urls.split(",")

    for url in urls:
        try:
            response = requests.get(url.strip(), headers=headers, timeout=5)
            response.raise_for_status()

            image = BytesIO(response.content)
            return send_file(image, mimetype=response.headers.get("Content-Type"))
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching image from {url}: {e}")
            continue

    return abort(500, "Error fetching image from all provided URLs")

@app.route("/stores")
def stores() -> Response:
    """Return store names for the selected dispensary as JSON."""
    dispensary = request.args.get("dispensary")
    if not dispensary:
        return abort(400, "Dispensary parameter is required")

    store_names = get_store_names(dispensary_name=dispensary, date=today)
    if not store_names:
        return abort(404, "Stores not found")

    return jsonify({"stores": store_names})

@app.route("/db-page", methods=["GET"])
def db_page() -> str:
    """Render the database page with filtered and sorted products."""
    dispensary = request.args.get("dispensary")
    category = request.args.get("category")
    store_name = request.args.get("store_name")
    sort = request.args.get("sort")
    limit = request.args.get("limit", default="100")

    conn = db_connection()
    if conn is None:
        return "Database connection failed."

    try:
        with conn.cursor() as cur:
            table_name = get_partitioned_table_name(today)
            query = SQL("SELECT * FROM {} WHERE date = %s").format(Identifier(table_name))
            filters = [str(today)]

            if dispensary:
                query += SQL(" AND dispensary_name = %s")
                filters.append(dispensary)
            if category:
                query += SQL(" AND product_category = %s")
                filters.append(category)
            if store_name:
                query += SQL(" AND store_name = %s")
                filters.append(store_name)

            if sort:
                sort_options = {
                    "product_potency_asc": "product_potency ASC",
                    "product_potency_desc": "product_potency DESC",
                    "product_price_asc": "product_price ASC",
                    "product_price_desc": "product_price DESC",
                    "product_size_asc": "product_size ASC",
                    "product_size_desc": "product_size DESC",
                }
                query += SQL(" ORDER BY {}").format(SQL(sort_options.get(sort, "")))

            query += SQL(" LIMIT %s")
            filters.append(limit)

            logging.info("Final Query: %s", query.as_string(conn))
            logging.info("Filters: %s", filters)
            cur.execute(query, filters)
            products = cur.fetchall()

    except Exception as err:
        logging.error(f"Error fetching products: {err}")
        products = []

    finally:
        conn.close()

    return render_template("db_page.html", data=products)

def hash_pw(password:str) -> str | bytes:
    hashed_pw = bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt())
    return hashed_pw

# Example route for login (commented out for now)
# @app.route("/login", methods=["POST"])
# def login():
#     username = request.form.get('username')
#     password = request.form.get('password')
#
#     if username and password:
#         conn = db_connection()
#         if conn is None:
#             return "Connection to db failed."
#
#         try:
#             with conn.cursor() as cur:
#                 table_name = os.getenv("USER_TABLE")
#                 query = SQL("SELECT id, username, hashed_pw FROM {} WHERE username = %s").format(Identifier(table_name))
#                 cur.execute(query, [username])
#                 user = cur.fetchone()
#                 if user and bcrypt.checkpw(password.encode(), user['hashed_pw'].encode()):
#                     return "Login successful!"
#                 else:
#                     return "Login failed!"
#         finally:
#             conn.close()
#
#     return "Missing username or password."

@app.route("/feedback")
def feedback():
    raise NotImplemented


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        user_name = request.form['name']
        user_email = request.form['email']
        user_message = request.form['message']

        try:
            msg = Message("New Contact Form Submission",
                          sender="twenty8cowsemail@gmail.com",  # Sender is your email
                          recipients=["twenty8cows@gmail.com"])  # The email goes to your inbox
            msg.body = f"Name: {user_name}\nEmail: {user_email}\n\nMessage:\n{user_message}"
            mail.send(msg)
            flash("Your email has been sent!", "success")
        except Exception as e:
            flash(f"Failed to send message: {str(e)}", "danger")

        # Render the template with the flash message
        return render_template('contact.html')

    return render_template('contact.html')



if __name__ == "__main__":
    app.run(debug=True)
