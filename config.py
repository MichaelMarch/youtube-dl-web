# TODO: implement configs as json files instead, cause this approach currently sucks
#       Some fields are requried and could maybe have default values or raise exception at startup
from os import environ as environment, path
from datetime import timedelta

if "FLASK_SECRET_KEY" not in environment:
    print("Unable to start application. Environment variable 'FLASK_SECRET_KEY' is missing.")
    exit(-1)


class Config:
    DEBUG: bool = False
    SECRET_KEY: str = environment["FLASK_SECRET_KEY"]
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(days=365)


class DevConfig(Config):
    DEBUG: bool = True
    TEST_USER_NAME: str = "test"
    TEST_USER_PASSWORD: str = "1234"
    TEST_USER_NAME2: str = "test2"
    TEST_USER_PASSWORD2: str = "123"
    YT_SAVE_PATH: str = "D:\\yt\\"


class ProdConfig(Config):
    YT_SAVE_PATH: str = "/home/"


app_config: dict[str, Config] = {
    "development": DevConfig,
    "production": ProdConfig,
}
