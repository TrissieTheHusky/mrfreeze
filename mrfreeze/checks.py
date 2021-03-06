"""Various checks that can be added to commands."""

from typing import Union

import discord
from discord import Member
from discord.ext.commands import Context, CheckFailure


class MuteCheckFailure(CheckFailure):
    pass

async def is_owner(ctx: Context) -> bool:
    """
    Check if author is the bot owner.

    Call with:
    @commands.check(checks.is_owner)
    """
    is_owner = await ctx.bot.is_owner(ctx.author)
    if not is_owner:
        await ctx.send(
            f"{ctx.author.mention} You're not the boss of me! " +
            "<@!154516898434908160> Help I'm being opressed!!")
    return is_owner


async def is_mod(caller: Union[Context, Member]) -> bool:
    """
    Check if the author is a mod.

    This check can be used with both context and member objects.
    Output varies depending on which object is used. For context
    objects the check will send a response to the user. For a
    member object the function simply returns True or False.

    Call with:
    @commands.check(checks.is_mod)
    """
    member_call = isinstance(caller, discord.member.Member)

    if member_call:
        # caller is a member object
        mod_status = caller.guild_permissions.administrator

    else:
        # caller is a context object
        if caller.guild is None:
            await caller.send(
                f"Don't you try to sneak into my DMs and mod me!")
            return False

        mod_status = caller.author.guild_permissions.administrator
        if not mod_status:
            await caller.send(
                f"{caller.author.mention} Only mods are " +
                "allowed to use that command.")

    return mod_status


async def always_allow(ctx: Context) -> bool:
    """
    Return True, always. Used for debugging.

    Call with:
    @commands.check(checks.always_deny)
    """
    return True


async def always_deny(ctx: Context) -> bool:
    """
    Return False, always. Used for debugging.

    Call with:
    @commands.check(checks.always_deny)
    """
    return False
