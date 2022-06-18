from http import HTTPStatus

from flask import Blueprint
from flask import current_app as app
from flask_pydantic import validate
from sqlalchemy.exc import IntegrityError

from exchange.currency_operations import buy_currency, sell_currency
from exchange.database import create_session
from exchange.models import (
    Currency,
    CurrencyOperation,
    CurrencyOperationType,
    User,
    Wallet,
)
from exchange.models_schema import (
    CurrencyModel,
    ExtendedCurrencyModel,
    OperationModel,
    QueryModel,
    RequestCurrencyModel,
    RequestUserModel,
    ResponseModel,
    StatusType,
    UserModel,
)

view_bp = Blueprint('view', __name__)


@view_bp.route('/currency/add', methods=['POST'])
@validate()
def add_currency(body: RequestCurrencyModel) -> tuple[ResponseModel, int]:
    try:
        with create_session() as session:
            exchange_rate = Currency.generate_exchange_rate(
                app.config['MIN_EXCHANGE_RATE'], app.config['MAX_EXCHANGE_RATE']
            )
            currency = Currency(exchange_rate=exchange_rate, name=body.name.lower())
            session.add(currency)
            session.flush()
            currency_data = CurrencyModel.from_orm(currency)

    except IntegrityError:
        return (
            ResponseModel(
                status=StatusType.ERROR,
                error='This cryptocurrency already exists!',
            ),
            HTTPStatus.CONFLICT,
        )

    return (
        ResponseModel(
            status=StatusType.OK,
            data=currency_data,
        ),
        HTTPStatus.OK,
    )


@view_bp.route('/currency/<currency_name>', methods=['GET'])
@validate()
def get_currency_info(currency_name: str) -> tuple[ResponseModel, int]:
    with create_session() as session:
        currency = (
            session.query(Currency).filter(Currency.name == currency_name).one_or_none()
        )

        if currency is None:
            return (
                ResponseModel(
                    status=StatusType.ERROR,
                    error='There is no such cryptocurrency!',
                ),
                HTTPStatus.NOT_FOUND,
            )

        currency_data = CurrencyModel.from_orm(currency)

        currency_ext = ExtendedCurrencyModel(
            **currency_data.dict(),
            buying_rate=currency.generate_buying_rate(app.config['COMMISSION_AMOUNT']),
            selling_rate=currency.generate_selling_rate(
                app.config['COMMISSION_AMOUNT']
            ),
        )

        return (
            ResponseModel(
                status=StatusType.OK,
                data=currency_ext,
            ),
            HTTPStatus.OK,
        )


@view_bp.route('/currency/all', methods=['GET'])
@validate()
def get_all_currencies() -> tuple[ResponseModel, int]:
    with create_session() as session:
        currencies = session.query(Currency).all()

        return (
            ResponseModel(
                status=StatusType.OK,
                data=list(map(CurrencyModel.from_orm, currencies)),
            ),
            HTTPStatus.OK,
        )


@view_bp.route('/user/registration', methods=['POST'])
@validate()
def register_user(body: RequestUserModel) -> tuple[ResponseModel, int]:
    try:
        with create_session() as session:
            new_user = User(name=body.name)
            session.add(new_user)
            session.flush()

            wallet = Wallet(user_id=new_user.id)
            session.add(wallet)
            session.flush()

            user_data = UserModel.from_orm(new_user)

    except IntegrityError:
        return (
            ResponseModel(
                status=StatusType.ERROR,
                error='The user already exists!',
            ),
            HTTPStatus.CONFLICT,
        )

    return (
        ResponseModel(
            status=StatusType.OK,
            data=user_data,
        ),
        HTTPStatus.OK,
    )


@view_bp.route('/user/<user_name>', methods=['GET'])
@validate()
def get_user_info(user_name: str) -> tuple[ResponseModel, int]:
    with create_session() as session:
        user = session.query(User).filter(User.name == user_name).one_or_none()

        if user is None:
            return (
                ResponseModel(
                    status=StatusType.ERROR,
                    error='There is no such user!',
                ),
                HTTPStatus.NOT_FOUND,
            )

        return (
            ResponseModel(
                status=StatusType.OK,
                data=UserModel.from_orm(user),
            ),
            HTTPStatus.OK,
        )


@view_bp.route('/user/<user_name>/operations', methods=['GET'])
@validate()
def get_user_operations_info(
    user_name: str, query: QueryModel
) -> tuple[ResponseModel, int]:
    with create_session() as session:
        user = session.query(User).filter(User.name == user_name).one_or_none()

        if user is None:
            return (
                ResponseModel(
                    status=StatusType.ERROR,
                    error='There is no such user!',
                ),
                HTTPStatus.NOT_FOUND,
            )

        operations = (
            session.query(CurrencyOperation)
            .filter(CurrencyOperation.wallet_id == user.wallet.id)
            .limit(query.limit)
            .offset(query.limit * query.page)
            .all()
        )

        return (
            ResponseModel(
                status=StatusType.OK,
                data=operations,
            ),
            HTTPStatus.OK,
        )


@view_bp.route('/trade', methods=['POST'])
@validate()
def make_operation(body: OperationModel) -> tuple[ResponseModel, int]:
    with create_session() as session:
        currency = (
            session.query(Currency)
            .filter(Currency.name == body.currency_name)
            .one_or_none()
        )

        if currency is None:
            return (
                ResponseModel(
                    status=StatusType.ERROR,
                    error='There is no such cryptocurrency!',
                ),
                HTTPStatus.NOT_FOUND,
            )

        user = session.query(User).filter(User.name == body.user_name).one_or_none()

        if user is None:
            return (
                ResponseModel(
                    status=StatusType.ERROR,
                    error='There is no such user!',
                ),
                HTTPStatus.NOT_FOUND,
            )

        if not currency.exchange_rate == body.exchange_rate:
            return (
                ResponseModel(
                    status=StatusType.ERROR,
                    error='You are trying to perform an operation '
                    'at an outdated exchange rate, please try again.',
                ),
                HTTPStatus.CONFLICT,
            )

        if body.operation == CurrencyOperationType.BUY:
            return buy_currency(session, user, currency, body.currency_amount)
        return sell_currency(session, user, currency, body.currency_amount)
