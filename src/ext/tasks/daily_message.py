from typing import *
import asyncio
import logging
from datetime import datetime, timedelta
import traceback
import json
from pprint import pformat

import lightbulb
from lightbulb.commands.base import OptionModifier as OM
import hikari
from hikari import Embed
from hikari.impl import MessageActionRowBuilder
import humanize
from apscheduler.triggers.interval import IntervalTrigger

from core import Table, getLogger, Inu
from utils import Colors, Reddit

log = getLogger(__name__)
bot: Inu

plugin = lightbulb.Plugin("daily_message")
table = Table("guilds")
ZELDA_RELEASE: datetime = datetime(2024, 9, 26) #TOTK: datetime(2023, 5, 12)
ZELDA_TITLE_FULL = "The Legend of Zelda: Echoes of Wisdom"
ZELDA_TITLE_PART = "Echoes of Wisdom"
ZELDA_REDDIT = "echoesofwisdom"

SYNCING = False


@plugin.listener(hikari.ShardReadyEvent)
async def load_tasks(event: hikari.ShardReadyEvent):
    """
    Loads task to update message once per day
    """
    global SYNCING
    if SYNCING:
        return
    else:
        SYNCING = True
    await asyncio.sleep(3)

    now = datetime.now()
    wait_to = datetime(now.year, now.month, now.day, 0, 5)
    if wait_to < now:
        wait_to += timedelta(days=1)
    secs = int((wait_to - now).total_seconds())
    log.info(f"updateing messages in {secs}s")
    await asyncio.sleep(secs)
    await update_messages()
    trigger = IntervalTrigger(days=1)
    plugin.bot.scheduler.add_job(update_messages, trigger)
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)



async def update_messages():
    """
    Updates messages from all guilds
    """
    try:
        await send_messages()
    except Exception:
        log.error(traceback.format_exc())


async def _send_message(guild_id: int, channel_id: int, message_id: int | None):
    """
    Creates embed, get kwargs for setup message and creates the message
    => updates the message_id in the db

    Description:
    ------------
    - deletes the given message with id <message_id>
    - creates a new message
    - updates the database
    """
    if message_id:
        try:
            await bot.rest.delete_message(channel_id, message_id)
        except Exception:
            pass
    delta = ZELDA_RELEASE - datetime.now()
    embed = Embed()
    embed.title = f"{ZELDA_TITLE_FULL} will be released in {humanize.naturaldelta(delta)} [{delta.days} days]"
    embed.description = (
        f"For more information take a look at [Google - {ZELDA_TITLE_PART}](https://www.google.com/search?q={'+'.join(ZELDA_TITLE_FULL.split(' '))})\n"
    )
    posts = await Reddit.get_posts(ZELDA_REDDIT, top=True, time_filter="week", minimum=4)
    embed.description += f"\nHere's what Reddit thinks about it:\n\n"
    for i, post in enumerate(posts):
        embed.description += f"{i+1}. | [{post.title}](https://www.reddit.com/r/{ZELDA_REDDIT}/comments/{post.id})\n\n"
    embed.color = Colors.from_name("royalblue")
    embed.set_thumbnail("https://media.discordapp.net/attachments/818871393369718824/1253064554242642031/14d316da5590a0821cbac3662d25cf4c.png?ex=66747ece&is=66732d4e&hm=5b78c832df09e523178b8bdbcb26aca3e802b657a6c532b24e30dec2faebb741&=&format=webp&quality=lossless&width=1320&height=856")
    embed.set_image("https://media.discordapp.net/attachments/818871393369718824/1253064282384371883/Echoes_of_Wisdom.png?ex=66747e8d&is=66732d0d&hm=b8a85531e59aa8016d6aaf9f01e547a392359bdae3b9b2b8191b41ae4ad96491&=&format=webp&quality=lossless&width=1320&height=660")
    message = await bot.rest.create_message(channel_id, embed=embed)
    await table.update(set={"message_id": message.id}, where={"guild_id": guild_id})



async def send_messages():
    """
    fetches DB entries, and sends for every single one the message
    """
    guild_records = await table.fetch(f"SELECT * FROM {table.name}")
    for r in guild_records:
        log.debug(f"send message")
        asyncio.create_task(_send_message(
            guild_id=r["guild_id"],
            channel_id=r["channel_id"],
            message_id=r["message_id"]
        ))



@plugin.listener(hikari.GuildLeaveEvent)
async def on_guild_leave(event: hikari.GuildLeaveEvent):
    """
    remove a guild from db when the bot gets kicked
    """
    table = Table("guilds")
    await table.execute(f"DELETE FROM {table.name} WHERE guild_id = $1", event.guild_id)
    log.info(f"Leaft guild with id {event.guild_id}")



@plugin.listener(hikari.InteractionCreateEvent)
async def on_join_interaction(event: hikari.InteractionCreateEvent):
    """
    manages the interactions of the startup message
    """
    try:
        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return
        i: hikari.ComponentInteraction = event.interaction
        try:
            dict_ = json.loads(event.interaction.custom_id)
            log.debug(event.interaction.custom_id)
            log.debug(pformat(dict_))
            guild_id = int(dict_["guild_id"])
            type_ = dict_["type"]
            channel_id = int(event.interaction.values[0])
        except Exception:
            log.warning(traceback.format_exc())
        
        if not type_ == "guild_join_menu":
            return
        await i.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE, 
            f"From now on I will send messages into <#{channel_id}>"
        )
        log.debug(i.values)
        await table.upsert(["guild_id", "channel_id"], values=[guild_id, channel_id])
        guild = await bot.rest.fetch_guild(guild_id)
        log.info(f"Added guild [{guild.id}] '{guild.name}' with channel_id {channel_id} to the DB")
        await _send_message(guild_id, channel_id, None)
    except hikari.ForbiddenError:
        await i.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE, 
            "I can't send messages there. - lacking on permissions. Make sure that I can send messages there"
        )
    except Exception:
        log.critical(traceback.format_exc())



@plugin.listener(hikari.GuildJoinEvent)
async def on_guild_join(event: hikari.GuildJoinEvent):
    """
    send setup message when bot joins guild
    """
    not_nsfw_channels = []
    channels = event.guild.get_channels()
    for channel_id, channel in channels.items():
        # removed nsfw check (not channel.is_nsfw)
        if isinstance(channel, hikari.TextableChannel) and not isinstance(channel, hikari.GuildVoiceChannel):
            not_nsfw_channels.append(channel)
        else:
            continue
    not_nsfw_channels.sort(key=lambda ch: ch.created_at)
    for channel in not_nsfw_channels:
        # try to send the message, until the bot was allowed to send a message into a channel
        try:
            message = await bot.rest.create_message(**create_settings_message_kwargs(event.guild, channel.id)) 
        except hikari.ForbiddenError:
            log.warning(f"Can't send message to channel {channel.id} - lacking on permissions")
            continue
        except Exception:
            log.error(traceback.format_exc())
        if message:
            break



@plugin.command
@lightbulb.command("set", "change the channel, where to send the message")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def set_channel(ctx: lightbulb.context.Context):
    """call setup message manually per slash command"""
    try:
        guild = ctx.get_guild()  
        if not guild:
            log.error(f"guild is not in cache. Change method to rest")
            return
        kwargs = create_settings_message_kwargs(guild, ctx.channel_id)
        del kwargs["channel"]
        await ctx.respond(**kwargs)
    except Exception:
        log.error(traceback.format_exc())



def create_settings_message_kwargs(guild: hikari.Guild, channel_id: int) -> Dict[str, Any]:
    """
    creates the kwargs for the startup message
    """
    custom_id = {
        "type": "guild_join_menu",
        "guild_id": str(guild.id),
        "id": str(bot.id_creator.create_id())
    }
    kwargs: Dict[str, Any] = {}
    kwargs["channel"] = channel_id
    kwargs["content"] = (
        f"Select the channel where I should send the daily {ZELDA_TITLE_PART} reminder message.\n"
        "If you need to create the channel or give me roles, that I see that specific channel "
        "then you can call this menu at anytime again with `/set` (this will update the channels I see).\n"
        "Keep in mind, that I can just show the first 24 channels of your guild.\n"
    )
    component = (
        MessageActionRowBuilder()
        .add_channel_menu(json.dumps(custom_id, indent=None))
    )
    # channels = guild.get_channels()
    # for ch_id, channel in channels.items():
    #     # not channel.is_nsfw 
    #     if isinstance(channel, hikari.TextableChannel) and not isinstance(channel, hikari.GuildVoiceChannel):
    #         pass
    #     else:
    #         continue
    #     component = component.add_option(str(channel.name), str(channel.id)).add_to_menu()
    # component = component.add_to_container()
    kwargs["component"] = component
    return kwargs
        


def load(inu: Inu):
    global bot
    bot = inu
    inu.add_plugin(plugin)