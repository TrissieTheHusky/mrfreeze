"""
This module contains the MrFreeze class, i.e. the actual bot.

MrFreeze is a modified version of discord.ext.commands.Bot.
It has a few features that are not included in the basic bot
and also servers as a hub for various common functions that
are used in many of the cogs.
"""

import datetime
import logging
import os
import sys
from typing import Any
from typing import Awaitable
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional

import discord
from discord import Guild
from discord import Member
from discord import Role
from discord import TextChannel
from discord.ext import commands
from discord.ext.commands import Context

# Importing MrFreeze submodules
from mrfreeze import colors, greeting
from mrfreeze import dbfunctions, server_settings, time
from mrfreeze.checks import MuteCheckFailure
from mrfreeze.database.settings import Settings


# Usage note!
# The bot supports adding periodic asynchronous checks through
# the function add_bg_task(task, name).
# task is the function (see below) you wish to add.
# name is just some string that's not very important but necessary nontheless.
#
# A basic check looks something like this:
# async def name(self, args):
#     await self.bot.wait_until_ready()
#     while not self.bot.is_closed():
#         await asyncio.sleep(NUMBER)
#         pass # Do stuff on loop
class ServerTuple(NamedTuple):
    """Class for holding various information about a given server."""

    trash:        TextChannel
    mute_channel: TextChannel
    mute_role:    Optional[Role]


class MrFreeze(commands.Bot):
    """The man, the bot, the legend. This is where the magic happens."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Get logger
        self.logger = logging.getLogger("MrFreeze")
        self.logger.debug("Setting up MrFreeze")

        # Dict in which to save all the background tasks.
        self.bg_tasks: Dict[str, Awaitable] = dict()

        # Dict in which to save the ServerTuple for each server.
        self.servertuples: Dict[int, ServerTuple] = dict()

        # Setting up imported functions so they can be accessed by all cogs
        self.logger.debug("Linking imported functions as own methods")
        self.extract_time = time.extract_time
        self.parse_timedelta = time.parse_timedelta
        self.read_server_setting = server_settings.read_server_setting
        self.write_server_setting = server_settings.write_server_setting
        self.create_server_settings = server_settings.create_server_settings
        self.db_connect = dbfunctions.db_connect
        self.db_create = dbfunctions.db_create
        self.db_time = dbfunctions.db_time

        # Check that the necessary directories exist and
        # are directories, otherwise create them.
        # All paths are relative to the working directory.
        self.logger.debug("Setting up required directories")
        self.db_prefix = "databases"
        self.path_setup(self.db_prefix, "DB prefix")
        self.servers_prefix = "config/servers"
        self.path_setup(self.servers_prefix, "Servers prefix")

        self.logger.debug("Instantiating Settings module")
        self.settings = Settings()

        # Add the mute check
        self.logger.debug("Adding self mute check")
        self.check(self.block_self_if_muted)

    async def block_self_if_muted(self, ctx: Context) -> bool:
        """Block commands form executing if MrFreeze is muted in a certain server."""
        command = ctx.command.name

        if self.settings.is_freeze_muted(ctx.guild) and command != "freezemute":
            server = ctx.guild.name
            author = ctx.author
            raise MuteCheckFailure(message=f"{author} @ {server}: {command}")

        return True

    async def on_ready(self) -> None:
        """Set the bot up, print some greeting messages and stuff."""
        # Set tuples up for all servers
        for server in self.guilds:
            await self.server_tuple(server)

        # Greeting (printed to console)
        greetmsg = greeting.bot_greeting(self)
        for line in greetmsg:
            self.logger.info(line)
        self.logger.info(colors.color_test())

        # Set activity to "Listening to your commands"
        await self.change_presence(
            status=None,
            activity=discord.Activity(
                name='your commands...',
                type=discord.ActivityType.listening
            )
        )

        # Signal to the terminal that the bot is ready.
        self.logger.info(f"{colors.WHITE_B}READY WHEN YOU ARE CAP'N!{colors.RESET}")

    def path_setup(self, path: str, trivial_name: str) -> None:
        """Create various directories which the bot needs."""
        if os.path.isdir(path):
            status =  f"{colors.GREEN_B}{trivial_name} {colors.GREEN}({path}) "
            status += f"{colors.CYAN}exists and is a directory.{colors.RESET}"
            self.logger.info(status)
        elif os.path.exists(path):
            status =  f"{colors.RED_B}{trivial_name} {colors.RED}({path}) "
            status += f"{colors.CYAN}exists but is not a directory. "
            status += f"Aborting.{colors.RESET}"
            self.logger.error(status)
            sys.exit(0)
        else:
            try:
                os.makedirs(path)
                status =  f"{colors.GREEN_B}{trivial_name} "
                status += f"{colors.GREEN}({path}){colors.CYAN} was "
                status += f"successfully created.{colors.RESET}"
                self.logger.info(status)
            except Exception as e:
                status =  f"{colors.RED_B}{trivial_name} {colors.RED}({path}) "
                status += f"{colors.CYAN} does not exist and could not be "
                status += f"created:\n{colors.RED}==> {e}{colors.RESET}"
                self.logger.error(status)
                sys.exit(0)

    async def server_tuple(self, server: Guild) -> None:
        """
        Create the server tuple for a given server.

        The purpose of the server tuple is to keep various information so
        that we won't have to make as many api calls to get channels from
        ids and so on.

        Avoid using this for now as it's not really in active use and doesn't
        get updated when the values are updated.
        """
        self.servertuples[server.id] = ServerTuple(
            await self.get_trash_channel(server),
            await self.get_mute_channel(server),
            await self.get_mute_role(server)
        )

    def add_bg_task(self, task, name: str) -> None:
        """
        Add a task to run in the background in the bot.

        Useful for periodic checks/updates.
        """
        self.bg_tasks[name] = self.loop.create_task(task)

    async def get_trash_channel(self, server: Guild) -> TextChannel:
        """
        Get the server's trash channel.

        If a server has specified a trash channel that channel is returned,
        if the server hasn't specified one the default system channel is
        returned instead.
        """
        channel_id = self.settings.get_trash_channel(server)

        if channel_id:
            channel = await self.fetch_channel(channel_id)
            return channel
        else:
            return server.system_channel

    async def get_mute_channel(self, server: Guild) -> TextChannel:
        """
        Get the server's mute channel.

        If a server has specified a mute channel that channel is returned,
        if the server hasn't specified one the default system channel is
        returned instead.
        """
        channel_id = self.settings.get_mute_channel(server)

        if channel_id:
            channel = await self.fetch_channel(channel_id)
            return channel
        else:
            return server.system_channel

    async def get_mute_role(self, guild: Guild) -> Optional[TextChannel]:
        """
        Get the server's mute role.

        If none is specified, try to find one called antarctica.
        If still none is found, return None.
        """
        for role in guild.roles:
            if role.name.lower() == "antarctica":
                return role
        return None

    def mentions_list(self, mentions: List[Member]) -> str:
        """Create a string of mentions from a list of user objects."""
        mentions = [user.mention for user in mentions]
        if len(mentions) == 0:
            return "No one"
        elif len(mentions) == 1:
            return mentions[0]
        else:
            return ", ".join(mentions[:-1]) + f" and {mentions[-1]}"

    def current_time(self) -> str:
        """Get good time stamps for consistent console messages throughout the bot."""
        formated_time = datetime.datetime.strftime(
            datetime.datetime.now(),
            "%Y-%m-%d %H:%M"
        )
        return f"{colors.CYAN_B}{formated_time}{colors.RESET}"
