import os
from typing import Optional, Type

from flask import Flask, current_app

from config import Config
from exchange.commands import init_db_command
from exchange.database import init_app
from exchange.rate_changer import RateChanger
from exchange.routes import view_bp


def start_rate_changer() -> None:
    app_rate_changer = RateChanger(
        current_app.config['CHANGER_SLEEP_TIME'],
        current_app.config['CHANGER_LOWER_BOUND'],
        current_app.config['CHANGER_UPPER_BOUND'],
    )
    app_rate_changer.start()


# Using "Optional" because config could be None; "Type[]" to accept subclasses
def create_app(config: Optional[Type[Config]] = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    if config is None:
        app.config.from_object(os.environ.get('APP_CONFIG', Config))
    else:
        app.config.from_object(config)

    init_app(app)

    app.register_blueprint(view_bp)

    app.cli.add_command(init_db_command)

    if app.config['IS_RATE_CHANGER']:
        app.before_first_request_funcs.append(start_rate_changer)

    return app
