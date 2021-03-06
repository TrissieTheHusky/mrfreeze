"""Cog for handling various errors that might arise when executing commands."""

import logging
import sys
import traceback

from discord.ext.commands import BadArgument
from discord.ext.commands import CheckFailure
from discord.ext.commands import CommandInvokeError
from discord.ext.commands import CommandNotFound
from discord.ext.commands import CommandOnCooldown
from discord.ext.commands import Context
from discord.ext.commands import MissingRequiredArgument
from discord.ext.commands.cooldowns import BucketType

import inflect

from mrfreeze.bot import MrFreeze
from mrfreeze.checks import MuteCheckFailure
from mrfreeze.colors import CYAN
from mrfreeze.colors import RED_B
from mrfreeze.colors import RESET
from mrfreeze.colors import WHITE_B

from .cogbase import CogBase


def setup(bot: MrFreeze) -> None:
    """Add the cog to the bot."""
    bot.add_cog(ErrorHandler(bot))


class ErrorHandler(CogBase):
    """How the bot acts when errors occur."""

    def __init__(self, bot: MrFreeze) -> None:
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @CogBase.listener()
    async def on_command_error(self, ctx: Context, error: Exception) -> None:
        """Determine what should happen when we encounter a command error."""
        username: str = f"{ctx.author.name}#{ctx.author.discriminator}"
        mention: str = ctx.author.mention
        invocation: str = f"{WHITE_B}{ctx.prefix}{ctx.invoked_with}"
        status: str

        if isinstance(error, MuteCheckFailure):
            status = f"{RED_B}MrFreeze is muted: {CYAN}{error}{RESET}"
            self.logger.error(status)
            return

        elif isinstance(error, CheckFailure):
            status  = f"{RED_B}Check failure: {CYAN}"
            status += f"{username} tried to illegaly invoke {invocation}{RESET}"
            self.logger.error(status)
            return

        elif isinstance(error, MissingRequiredArgument):
            status  = f"{RED_B}Check failure: {CYAN}"
            status += f"{username} tried executing {invocation} with too "
            status += f"few arguments{RESET}"
            self.logger.error(status)

            reply  = f"{ctx.author.mention} You need to specify some arguments to invoke "
            reply += f"{ctx.prefix}{ctx.invoked_with}, or I won't know what to do."
            await ctx.send(reply)
            return

        elif isinstance(error, BadArgument):
            status  = f"{RED_B}Bad arguments: {CYAN}{username} "
            status += f"while using command {invocation}{RESET}"
            self.logger.error(status)
            self.logger.error(error)

            reply = f"{mention} That's not quite the information I need to execute that command."
            await ctx.send(reply)
            return

        elif isinstance(error, CommandNotFound):
            status  = f"{RED_B}Command not found: {CYAN}"
            status += f"{username} tried to use {invocation}{RESET}"
            self.logger.error(status)
            return

        elif isinstance(error, CommandInvokeError):
            # On Timeout Error, a CommandInvokeError containing the original
            # error is returned. Not the original TimeoutError itself.
            error_name: str = type(error.original).__name__
            status  = f"{RED_B}{error_name}: {CYAN}"
            status += f"{username} tried to use {invocation}{RESET}"
            self.logger.error(status)
            return

        elif isinstance(error, CommandOnCooldown):
            if error.cooldown.rate == 1:
                er_rate = "once"
            elif error.cooldown.rate == 2:
                er_rate = "twice"
            else:
                infl = inflect.engine()
                er_rate = infl.number_to_words(error.cooldown.rate) + " times"

            er_per_sec = int(error.cooldown.per)
            er_retry_sec = int(error.retry_after)

            def seconds_parse(time_input: int) -> str:
                if time_input > 60:
                    input_min = int(time_input / 60)
                    input_sec = int(time_input - (input_min * 60))
                    if input_sec != 0:
                        return f"{input_min} min {input_sec} sec"
                    else:
                        return f"{input_min} min"
                else:
                    return f"{er_retry_sec} sec"

            er_per = seconds_parse(er_per_sec)
            er_retry = seconds_parse(er_retry_sec)

            bucket = error.cooldown.type
            if bucket == BucketType.user:
                er_type = " per user"
            elif bucket == BucketType.member:
                er_type = " per member"
            elif bucket == BucketType.guild:
                er_type = " per server"
            elif bucket == BucketType.channel:
                er_type = " per channel"
            # Coming in discord.py 1.3
            # elif bucket == BucketType.role:
            #     er_type = " per role"
            elif bucket == BucketType.category:
                er_type = " per channel category"
            else:
                er_type = ""

            reply  = f"{mention} The command **{ctx.prefix}{ctx.invoked_with}** can only be used "
            reply += f"{er_rate} every {er_per}{er_type}.\nTry again in {er_retry}."
            await ctx.send(reply)

        else:
            # Who knows what happened? The stack trace, that's who.
            status  = f"{RED_B}Unclassified error: "
            status += f"{WHITE_B}{error}{RESET}"
            self.logger.error(status)
            traceback.print_exception(
                type(error),
                error,
                error.__traceback__,
                file=sys.stderr
            )
