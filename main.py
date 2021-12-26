import asyncio
import logging

import src.context.db as db
from src.controllers.bot import bot
from src.parser import parsing_loop


async def main():
    logging.basicConfig(level=logging.INFO)

    await db.init()

    await asyncio.gather(
        asyncio.create_task(parsing_loop()),
        asyncio.create_task(bot.run_polling())
    )


if __name__ == "__main__":
    asyncio.run(main())
