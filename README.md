Florida MMJ Price Tracker
Overview
Florida MMJ Price Tracker is a web application that provides up-to-date pricing information for medical marijuana products across dispensaries in the Florida legal market. This application aggregates data from various dispensaries and presents it in an easy-to-navigate interface, helping patients find the best prices for their needs.

Features
Real-Time Price Updates: Automatically updates prices from multiple dispensaries across Florida.
Comprehensive Product Listings: Includes a wide range of products, such as flower, concentrates, edibles, and more.
Search and Filter: Easily search for specific products and filter results by dispensary, product type, potency, and price.
Responsive Design: Optimized for desktop and mobile devices, ensuring a smooth user experience on any platform.
Custom Alerts: Set up alerts to be notified when your favorite products drop in price.
Installation
To set up the Florida MMJ Price Tracker on your local machine, follow these steps:

Prerequisites
Python 3.12 (or higher)
Flask (for the web application)
PostgreSQL (for the database)
Git (for version control)
Mailgun API (for email notifications)
Clone the Repository
bash
Copy code
git clone https://github.com/yourusername/florida-mmj-price-tracker.git
cd florida-mmj-price-tracker
Set Up Environment Variables
Create a .env file in the root directory of your project and add the following environment variables:

env
Copy code
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=postgresql://username:password@localhost:5432/mmj_price_tracker
MAILGUN_DOMAIN=yourdomain.com
MAILGUN_API_KEY=your-mailgun-api-key
Install Dependencies
bash
Copy code
pip install -r requirements.txt
Database Setup
Create the PostgreSQL database:

bash
Copy code
createdb mmj_price_tracker
Run database migrations:

bash
Copy code
flask db upgrade
Run the Application
bash
Copy code
flask run
Visit the app at http://localhost:5000 in your web browser.

Usage
Browse Products: Explore different medical marijuana products available in Florida's dispensaries.
Search and Filter: Use the search bar and filters to narrow down your options.
Set Alerts: Get notified via email when the price of your favorite products changes.
Contributing
We welcome contributions from the community! To contribute:

Fork the repository.
Create a new branch (git checkout -b feature/your-feature).
Commit your changes (git commit -m 'Add some feature').
Push to the branch (git push origin feature/your-feature).
Open a pull request.
License
This project is licensed under the MIT License. See the LICENSE file for more details.

Contact
For any questions or support, please contact Jonathan Mitchell at jonathan@edenflorida.com.

