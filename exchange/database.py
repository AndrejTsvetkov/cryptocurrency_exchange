from contextlib import contextmanager
from typing import Any, Generator

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# здесь не мог сделать инициализацию, потому что не было доступно приложение
session_factory = sessionmaker()
# for thread safety
Session = scoped_session(session_factory)


# generator typing 1) the type returned with each iteration,
# 2) the type that the generator will receive (send method),
# 3) The type that will be returned when the generator exits altogether.
@contextmanager
def create_session() -> Generator[scoped_session, None, None]:
    new_session = Session()

    try:
        yield new_session
        new_session.commit()
    except Exception:
        new_session.rollback()
        raise
    finally:
        new_session.close()


def init_app(app: Flask, **kwargs: Any) -> Flask:
    db_engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], **kwargs)  # type: ignore

    # bind database engine using by our app to our session factory
    Session.configure(
        bind=db_engine,
        expire_on_commit=app.config['EXPIRE_ON_COMMIT'],
    )

    app.db_engine = db_engine  # type: ignore

    # ??
    return app
