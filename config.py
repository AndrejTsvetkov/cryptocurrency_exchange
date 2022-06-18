from decimal import Decimal
from pathlib import Path


basedir = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = 'changeme'
    TESTING = False

    # database config
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{basedir / "data.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXPIRE_ON_COMMIT = True

    # To generate a currency exchange rate
    MIN_EXCHANGE_RATE = 1
    MAX_EXCHANGE_RATE = 100
    COMMISSION_AMOUNT = Decimal('0.06')

    # To automatically rate change
    IS_RATE_CHANGER = True
    CHANGER_SLEEP_TIME = 10  # in seconds
    CHANGER_LOWER_BOUND = -10  # in percent, "-" means cost reduction
    # In general, the exchange rate increases over time, so we model this behaviour a bit
    CHANGER_UPPER_BOUND = 11  # in percent

    DEFAULT_CURRENCIES = ('bitcoin', 'ethereum', 'ripple', 'monero', 'cardano')


class ProductionConfig(Config):
    SECRET_KEY = '9GxfbhM56iKo112kjlsglq'


class TestConfig(Config):
    TESTING = True
    EXPIRE_ON_COMMIT = False
    IS_RATE_CHANGER = False
    SERVER_NAME = 'localhost.localdomain'
