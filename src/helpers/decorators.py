import asyncio
from typing import Union, NoReturn, Callable
import logging


def async_infinity_loop(delay: Union[float, int]) -> Callable:
    def decorator(function) -> Callable:
        async def decorated_function(*args) -> NoReturn:
            while True:
                try:
                    await function(*args)
                    await asyncio.sleep(delay)
                except Exception as e:
                    logging.error(e)

        return decorated_function

    return decorator
