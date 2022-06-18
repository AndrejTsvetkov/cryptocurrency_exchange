import click
from flask import Flask, current_app
from flask.cli import with_appcontext

from exchange.database import create_session
from exchange.models import Base, Currency


def fill_db(app: Flask) -> None:
    with create_session() as session:
        # здесь мы бы смогли использовать current_app,
        # приложение доступно так как мы работаем из-под функции с декоратором with_appcontext
        for currency_name in app.config['DEFAULT_CURRENCIES']:
            exchange_rate = Currency.generate_exchange_rate(
                app.config['MIN_EXCHANGE_RATE'], app.config['MAX_EXCHANGE_RATE']
            )
            currency = Currency(name=currency_name, exchange_rate=exchange_rate)
            session.add(currency)


@click.command('init_db')
@with_appcontext
def init_db_command() -> None:
    app = current_app
    Base.metadata.create_all(app.db_engine)  # type: ignore
    fill_db(app)
