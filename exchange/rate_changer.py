import time
from decimal import Decimal
from random import randrange
from threading import Thread

from exchange.database import create_session
from exchange.models import Currency


class RateChanger(Thread):
    def __init__(
        self,
        sleep_time: int,
        changer_lower_bound: int,
        changer_upper_bound: int,
    ):
        super().__init__()
        self.sleep_time = sleep_time
        self.lower_bound = changer_lower_bound
        self.upper_bound = changer_upper_bound

    def run(self) -> None:
        while True:
            time.sleep(self.sleep_time)

            with create_session() as session:
                for currency in session.query(Currency).all():
                    percent_change = self.generate_random_decimal(
                        self.lower_bound, self.upper_bound
                    )
                    currency.exchange_rate = currency.exchange_rate * (
                        1 + percent_change
                    )

    @staticmethod
    def generate_random_decimal(lower_bound: int, upper_bound: int) -> Decimal:
        return Decimal(randrange(lower_bound, upper_bound)) / 100
