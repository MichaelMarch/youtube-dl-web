from flask import Flask
from os import getenv

config_name: str = getenv("FLASK_ENV", "development")
app: Flask = Flask(__name__)

if True:
    from config import app_config
    
app.config.from_object(app_config[config_name])

if True:
    from app import routes


if __name__ == "__main__":
    # check if ffmpeg is installed
    app.run()
