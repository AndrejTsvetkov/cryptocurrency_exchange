from datetime import datetime
from decimal import Decimal
from enum import Enum
from random import randint

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta  # for mypy

Base: DeclarativeMeta = declarative_base()


class CurrencyOperationType(Enum):
    BUY = 'buy'
    SELL = 'sell'


class User(Base):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(10), unique=True, nullable=False)
    registration_date = sa.Column(sa.DateTime(), default=datetime.now(), nullable=False)

    # (User, Wallet) - one to one relationship
    wallet = relationship('Wallet', back_populates='user', uselist=False)


class Wallet(Base):
    __tablename__ = 'wallet'
    __table_args__ = (sa.CheckConstraint('balance >= 0'),)

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id))
    balance = sa.Column(sa.Numeric(10, 8), default=1000, nullable=False)

    # (Wallet, User) - one to one relationship
    user = relationship('User', back_populates='wallet')

    # (Wallet, CurrencyInWallet) - one to many relationship
    currencies = relationship('CurrencyInWallet', back_populates='wallet', uselist=True)

    # (Wallet, CurrencyOperation) - one to many relationship
    operations = relationship(
        'CurrencyOperation', back_populates='wallet', uselist=True
    )


class Currency(Base):
    __tablename__ = 'currency'
    __table_args__ = (sa.CheckConstraint('exchange_rate > 0'),)

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(10), unique=True, nullable=False)
    exchange_rate = sa.Column(sa.Numeric(10, 8), nullable=False)

    @staticmethod
    def generate_exchange_rate(
        min_exchange_rate: int, max_exchange_rate: int
    ) -> Decimal:
        return Decimal(randint(min_exchange_rate, max_exchange_rate))

    def generate_buying_rate(self, commission_amount: Decimal) -> Decimal:
        return self.exchange_rate * (1 + commission_amount)

    def generate_selling_rate(self, commission_amount: Decimal) -> Decimal:
        return self.exchange_rate * (1 - commission_amount)


class CurrencyInWallet(Base):
    __tablename__ = 'currency_in_wallet'
    __table_args__ = (sa.CheckConstraint('currency_amount > 0'),)

    id = sa.Column(sa.Integer, primary_key=True)
    currency_amount = sa.Column(sa.Numeric(10, 8), nullable=False)
    currency_id = sa.Column(sa.Integer, sa.ForeignKey(Currency.id))
    wallet_id = sa.Column(sa.Integer, sa.ForeignKey(Wallet.id))

    # (Wallet, CurrencyInWallet) - one to many relationship
    wallet = relationship('Wallet', back_populates='currencies', uselist=False)


class CurrencyOperation(Base):
    __tablename__ = 'currency_operation'

    id = sa.Column(sa.Integer, primary_key=True)
    currency_id = sa.Column(sa.Integer, sa.ForeignKey(Currency.id))
    wallet_id = sa.Column(sa.Integer, sa.ForeignKey(Wallet.id))
    type = sa.Column(sa.Enum(CurrencyOperationType), nullable=False)
    amount = sa.Column(sa.Numeric(10, 8), nullable=False)

    # (Wallet, CurrencyOperation) - one to many relationship
    wallet = relationship('Wallet', back_populates='operations', uselist=False)
