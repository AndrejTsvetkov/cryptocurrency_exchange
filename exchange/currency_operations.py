from decimal import Decimal
from http import HTTPStatus

from flask import current_app as app
from sqlalchemy.orm import Session

from exchange.models import (
    Currency,
    CurrencyInWallet,
    CurrencyOperation,
    CurrencyOperationType,
    User,
)
from exchange.models_schema import ResponseModel, StatusType


def buy_currency(
    session: Session, user: User, currency: Currency, currency_amount: Decimal
) -> tuple[ResponseModel, int]:
    exchange_rate = currency.generate_buying_rate(app.config['COMMISSION_AMOUNT'])
    if user.wallet.balance < exchange_rate * currency_amount:
        return (
            ResponseModel(
                status=StatusType.ERROR,
                error='You do not have enough money to make this transaction',
            ),
            HTTPStatus.CONFLICT,
        )

    user.wallet.balance -= exchange_rate * currency_amount

    currency_operation = CurrencyOperation(
        currency_id=currency.id,
        wallet_id=user.wallet.id,
        type=CurrencyOperationType.BUY,
        amount=currency_amount,
    )
    session.add(currency_operation)

    currency_in_wallet = (
        session.query(CurrencyInWallet)
        .filter(CurrencyInWallet.currency_id == currency.id)
        .one_or_none()
    )
    # if we don't have yet this currency in the wallet
    if currency_in_wallet is None:
        currency_in_wallet = CurrencyInWallet(
            currency_id=currency.id,
            wallet_id=user.wallet.id,
            currency_amount=currency_amount,
        )
        session.add(currency_in_wallet)
    # if we have this currency in the wallet just update its amount
    else:
        currency_in_wallet.currency_amount += currency_amount

    return (
        ResponseModel(
            status=StatusType.OK,
        ),
        HTTPStatus.OK,
    )


def sell_currency(
    session: Session, user: User, currency: Currency, currency_amount: Decimal
) -> tuple[ResponseModel, int]:
    exchange_rate = currency.generate_selling_rate(app.config['COMMISSION_AMOUNT'])

    # check if such cryptocurrency exists in the wallet
    for currency_in_wallet in user.wallet.currencies:
        if currency_in_wallet.currency_id == currency.id:
            current_currency = currency_in_wallet
            break
    else:
        return (
            ResponseModel(
                status=StatusType.ERROR,
                error='You do not have that currency',
            ),
            HTTPStatus.CONFLICT,
        )

    # check if the user have enough currency to sell
    if current_currency.currency_amount >= currency_amount:
        current_currency.currency_amount -= currency_amount
        user.wallet.balance += exchange_rate * currency_amount
    else:
        return (
            ResponseModel(
                status=StatusType.ERROR,
                error='You are trying to sell more currency than you have in your wallet',
            ),
            HTTPStatus.CONFLICT,
        )

    # If the user runs out of such currency, delete the entry
    if current_currency.currency_amount == Decimal('0'):
        session.delete(current_currency)

    currency_operation = CurrencyOperation(
        currency_id=currency.id,
        wallet_id=user.wallet.id,
        type=CurrencyOperationType.SELL,
        amount=currency_amount,
    )
    session.add(currency_operation)

    return (
        ResponseModel(
            status=StatusType.OK,
        ),
        HTTPStatus.OK,
    )
