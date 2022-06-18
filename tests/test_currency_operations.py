from decimal import Decimal
from http import HTTPStatus

import pytest

from exchange.currency_operations import buy_currency, sell_currency
from exchange.database import create_session
from exchange.models import Currency, CurrencyInWallet, User, Wallet


@pytest.mark.parametrize(
    ('exchange_rate', 'currency_amount', 'expected_result'),
    [
        (Decimal('2000'), Decimal('1'), HTTPStatus.CONFLICT),
        (Decimal('100'), Decimal('3'), HTTPStatus.OK),
    ],
    ids=['user_do_not_have_enough_money', 'success'],
)
def test_buy_currency(exchange_rate, currency_amount, expected_result):
    with create_session() as session:
        user = User(id=1, name='username')
        session.add(user)
        wallet = Wallet(id=1, user_id=1)
        session.add(wallet)
        currency = Currency(id=1, name='bitcoin', exchange_rate=exchange_rate)
        session.add(currency)
        session.flush()

        response = buy_currency(session, user, currency, currency_amount)

    assert response[1] == expected_result


@pytest.mark.parametrize(
    ('currency_to_sell', 'currency_amount', 'expected_result'),
    [
        (
            Currency(id=2, name='litecoin', exchange_rate=Decimal('100')),
            Decimal('1'),
            HTTPStatus.CONFLICT,
        ),
        (
            Currency(id=1, name='bitcoin', exchange_rate=Decimal('1000')),
            Decimal('100'),
            HTTPStatus.CONFLICT,
        ),
        (
            Currency(id=1, name='bitcoin', exchange_rate=Decimal('1000')),
            Decimal('3'),
            HTTPStatus.OK,
        ),
        (
            Currency(id=1, name='bitcoin', exchange_rate=Decimal('1000')),
            Decimal('20'),
            HTTPStatus.OK,
        ),
    ],
    ids=[
        'user_do_not_have_such_currency',
        'trying_to_sell_more_than_user_have ',
        'success',
        'sell_full_amount',
    ],
)
def test_sell_currency(currency_to_sell, currency_amount, expected_result):
    with create_session() as session:
        user = User(id=1, name='username')
        session.add(user)
        session.add(Wallet(id=1, user_id=1))
        session.add(Currency(id=1, name='bitcoin', exchange_rate=Decimal('1000')))
        session.add(Currency(id=2, name='litecoin', exchange_rate=Decimal('100')))
        session.add(
            CurrencyInWallet(id=1, currency_amount=20, currency_id=1, wallet_id=1)
        )
        session.flush()

        response = sell_currency(session, user, currency_to_sell, currency_amount)

    assert response[1] == expected_result
