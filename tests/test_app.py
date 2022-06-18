# pylint: disable=too-many-lines
# pylint: disable = too-many-arguments
from decimal import Decimal
from http import HTTPStatus

import pytest
from flask import url_for

from exchange.database import create_session
from exchange.models import (
    Currency,
    CurrencyInWallet,
    CurrencyOperation,
    CurrencyOperationType,
    User,
    Wallet,
)


def test_get_all_currencies(client):
    with create_session() as session:
        session.add(Currency(id=1, name='bitcoin', exchange_rate=Decimal('45717')))
        session.add(Currency(id=2, name='ethereum', exchange_rate=Decimal('3425.48')))

    assert client.get('/currency/all').get_json() == {
        'status': 'ok',
        'data': [
            {'id': 1, 'name': 'bitcoin', 'exchange_rate': 45717.0},
            {'id': 2, 'name': 'ethereum', 'exchange_rate': 3425.48},
        ],
        'error': None,
    }


@pytest.mark.parametrize(
    ('name', 'result_name'),
    [
        ('bitcoin', 'bitcoin'),
        ('Litecoin', 'litecoin'),
        ('RIPPLE', 'ripple'),
    ],
)
def test_add_currency(client, name, result_name):
    response = client.post('/currency/add', json={'name': name})
    assert response.status_code == HTTPStatus.OK

    with create_session() as session:
        currency = session.query(Currency).filter(Currency.name == result_name).first()
    assert currency.name == result_name


def test_add_already_existing_currency(client):
    with create_session() as session:
        session.add(Currency(id=1, name='dash', exchange_rate=Decimal('45717')))

    response = client.post('/currency/add', json={'name': 'dash'})
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.get_json() == {
        'status': 'error',
        'data': None,
        'error': 'This cryptocurrency already exists!',
    }


@pytest.mark.parametrize(
    ('id_', 'name', 'exchange_rate'),
    [
        (1, 'bitcoin', 45717.0),
        (2, 'litecoin', 0.1),
        (3, 'ripple', 234.1),
    ],
)
def test_get_currency_info(client, id_, name, exchange_rate):
    with create_session() as session:
        session.add(Currency(id=id_, name=name, exchange_rate=exchange_rate))

    response = client.get(url_for('view.get_currency_info', currency_name=name))
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()['data']
    assert data['id'] == id_
    assert data['name'] == name
    assert data['exchange_rate'] == exchange_rate
    assert data['buying_rate'] is not None
    assert data['selling_rate'] is not None


def test_get_currency_info_error(client):
    response = client.get(
        url_for('view.get_currency_info', currency_name='not_existing_currency')
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.get_json() == {
        'status': 'error',
        'data': None,
        'error': 'There is no such cryptocurrency!',
    }


def test_register_user(client):
    response = client.post('/user/registration', json={'name': 'username'})
    assert response.status_code == HTTPStatus.OK

    with create_session() as session:
        user = session.query(User).filter(User.name == 'username').first()
        wallet = user.wallet

    assert user.name == 'username'
    assert user.registration_date is not None

    assert wallet is not None
    assert wallet.balance == Decimal('1000')


def test_register_already_existing_user(client):
    with create_session() as session:
        session.add(User(id=1, name='username'))

    response = client.post('/user/registration', json={'name': 'username'})
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.get_json() == {
        'status': 'error',
        'data': None,
        'error': 'The user already exists!',
    }


def test_get_user_info(client):
    with create_session() as session:
        session.add(User(id=1, name='username'))
        wallet = Wallet(user_id=1)
        session.add(wallet)

    response = client.get(url_for('view.get_user_info', user_name='username'))
    assert response.status_code == HTTPStatus.OK
    data = response.get_json()['data']
    assert data['name'] == 'username'
    assert data['registration_date'] is not None


def test_get_user_info_error(client):
    response = client.get(url_for('view.get_user_info', user_name='not_existing_user'))

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.get_json() == {
        'status': 'error',
        'data': None,
        'error': 'There is no such user!',
    }


@pytest.mark.parametrize(
    ('limit', 'page', 'expected_len_of_items'),
    [
        (1, 0, 1),
        (1, 3, 0),
        (2, 0, 2),
        (2, 1, 1),
        (4, 0, 3),
    ],
    ids=[
        'one_operation_per_page',
        'operations_are_over',
        'two_operations_per_page',
        'one_operation_left',
        'all_operations',
    ],
)
def test_get_user_operations_info(client, limit, page, expected_len_of_items):
    with create_session() as session:
        session.add(User(id=1, name='username'))
        wallet = Wallet(id=1, user_id=1)
        session.add(wallet)
        session.add(
            CurrencyOperation(
                id=1,
                currency_id=1,
                wallet_id=1,
                type=CurrencyOperationType.BUY,
                amount=Decimal('1.2'),
            )
        )
        session.add(
            CurrencyOperation(
                id=2,
                currency_id=2,
                wallet_id=1,
                type=CurrencyOperationType.SELL,
                amount=Decimal('2.1'),
            )
        )
        session.add(
            CurrencyOperation(
                id=3,
                currency_id=3,
                wallet_id=1,
                type=CurrencyOperationType.BUY,
                amount=Decimal('10'),
            )
        )

    response = client.get(
        url_for(
            'view.get_user_operations_info',
            user_name='username',
            limit=limit,
            page=page,
        )
    )
    assert response.status_code == HTTPStatus.OK

    json_response = response.get_json()
    assert len(json_response['data']) == expected_len_of_items


def test_get_user_operations_info_error(client):
    response = client.get(
        url_for('view.get_user_operations_info', user_name='username', limit=1, page=0)
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.get_json() == {
        'status': 'error',
        'data': None,
        'error': 'There is no such user!',
    }


@pytest.mark.parametrize(
    (
        'currency_name',
        'user_name',
        'operation',
        'currency_amount',
        'exchange_rate',
        'expected_result',
    ),
    [
        (
            'ripple',
            'username',
            'buy',
            Decimal('1'),
            Decimal('100'),
            HTTPStatus.NOT_FOUND,
        ),
        (
            'bitcoin',
            'otheruser',
            'buy',
            Decimal('1'),
            Decimal('100'),
            HTTPStatus.NOT_FOUND,
        ),
        (
            'bitcoin',
            'username',
            'buy',
            Decimal('1'),
            Decimal('99.2'),
            HTTPStatus.CONFLICT,
        ),
        ('bitcoin', 'username', 'buy', Decimal('1'), Decimal('100'), HTTPStatus.OK),
        ('bitcoin', 'username', 'sell', Decimal('1'), Decimal('100'), HTTPStatus.OK),
    ],
    ids=[
        'there_is_no_such_cryptocurrency',
        'there_is_no_such_user',
        'outdated_exchange_rate',
        'success',
        'success',
    ],
)
def test_make_operation(
    client,
    currency_name,
    user_name,
    operation,
    currency_amount,
    exchange_rate,
    expected_result,
):
    with create_session() as session:
        user = User(id=1, name='username')
        session.add(user)
        session.add(Wallet(id=1, user_id=1))
        session.add(Currency(id=1, name='bitcoin', exchange_rate=Decimal('100')))
        session.add(
            CurrencyInWallet(id=1, currency_amount=20, currency_id=1, wallet_id=1)
        )
        session.flush()

    response = client.post(
        '/trade',
        json={
            'currency_name': currency_name,
            'user_name': user_name,
            'operation': operation,
            'currency_amount': currency_amount,
            'exchange_rate': exchange_rate,
        },
    )

    assert response.status_code == expected_result
