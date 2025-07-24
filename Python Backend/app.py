# app.py

from flask import Flask
from routes import maintenance_bp
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

# Register the blueprint
app.register_blueprint(maintenance_bp)

if __name__ == '__main__':
    # Run the Flask app. For production, use a production-ready WSGI server like Gunicorn or uWSGI.
    app.run(debug=True, port=8085)
