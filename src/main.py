"""The entrance point of the bot"""
import logging
import traceback
import time

import aiohttp
from core import LoggingHandler
logging.setLoggerClass(LoggingHandler)

import hikari
import lightbulb
from core import Inu, Table
from core import getLogger
from utils import Reddit


log = getLogger(__name__)
log.info(f"hikari version:{hikari.__version__}")
log.info(f"lightbulb version:{lightbulb.__version__}")

def main():
    log.info("Create TotK-bot")
    inu = Inu()
    print(inu.conf)

    @inu.listen(lightbulb.LightbulbStartedEvent)
    async def sync_prefixes(event: hikari.ShardReadyEvent):
        await Reddit.init_reddit_credentials(event.app)

    @inu.listen(hikari.StartingEvent)
    async def on_ready(event : hikari.StartingEvent):
        try:
            await inu.init_db()

        except Exception:
            log.critical(f"Can't connect Database to classes: {traceback.format_exc()}")

        # update bot start value
        # try:
        #     table = Table("bot")
        #     record = await table.select_row(["key"], ["restart_count"])
        #     if not record:
        #         count = 1
        #     else:
        #         count = int(record["value"])
        #         count += 1
        #     inu.restart_num = count
        #     await table.upsert(["key", "value"], ["restart_count", str(count)])
        #     log.info(f'RESTART NUMBER: {(await table.select_row(["key"], ["restart_count"]))["value"]}')
        # except Exception:
        #     log.error(traceback.format_exc())


    @inu.listen(lightbulb.LightbulbStartedEvent)
    async def on_bot_ready(event : lightbulb.LightbulbStartedEvent):
        pass
        # table = Table("bot")
        # record = await table.select_row(["key"], ["restart_count"])
        # activity = str(record["value"])
        # try:
        #     async with aiohttp.ClientSession() as session:
        #         resp = await session.get(f"http://numbersapi.com/{activity}")
        #         new_activity = (await resp.read()).decode("utf-8")
        #         activity = activity if len(activity) > len(new_activity) else new_activity
        # except Exception:
        #     log.error(traceback.format_exc())
        # await event.bot.update_presence(
        #     status=hikari.Status.IDLE, 
        #     activity=hikari.Activity(
        #         name=activity,
        #     )
        # )


    # @inu.listen(lightbulb.events.CommandInvocationEvent)
    # async def on_event(event: lightbulb.events.CommandInvocationEvent):
    #     log.debug(
    #         (
    #             f"[{event.context.user.id}] {event.context.author.username} called {event.command.name}"
    #         )
    #     )
    
    stop = False
    while not stop:
        try:
            inu.run()
            print(f"Press Strl C again to exit")
            time.sleep(3)
        except KeyboardInterrupt:
            stop = True
            log.waring(f"Keyboard interrupt - stop session")
            break
        except Exception:
            log.critical(f"Bot crashed with critical Error:")
            log.critical(traceback.format_exc())
        finally:
            if not inu.conf.bot.reboot:
                stop = True
            else:
                log.info(f"Rebooting bot")
    log.info(f"Bot shutted down!")

if __name__ == "__main__":
    main()
