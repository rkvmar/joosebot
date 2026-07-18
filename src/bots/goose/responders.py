import asyncio
import discord
import random
import os
import termcolor

from bots import utils as butils
from bots.goose import utils, sounds

async def command(client: discord.Client, message: discord.Message) -> None:
    if message.content.startswith('$gamble '):
        await butils.parse_gamble(message)

    # if message.content.startswith('!roulette'):
    #     await butils.parse_roulette(message)

    # if message.content.startswith('!chancetime'):
    #     await butils.chance_time(message, 1)

    if message.content.startswith('$coins'):
        # claude tries to pages
        leaderboard = butils.get_all_coins()
        if not leaderboard:
            await message.channel.send('no joosecoins yet!')
            return

        all_lines = [
            f'{rank}. <@{user_id}> — {amount} joosecoins'
            for rank, (user_id, amount) in enumerate(leaderboard, 1)
        ]

        chunk_size = 10
        pages = [
            '\n'.join(all_lines[i:i + chunk_size])
            for i in range(0, len(all_lines), chunk_size)
        ]

        parts = message.content.split()
        page = 0
        if len(parts) > 1:
            try:
                requested = int(parts[1])
                if 1 <= requested <= len(pages):
                    page = requested - 1
                else:
                    await message.reply(f'page must be between 1 and {len(pages)}')
                    return
            except ValueError:
                await message.reply(f'"{parts[1]}" isn\'t a valid page number')
                return

        lines = [f'**joosecoin leaderboard** (page {page + 1}/{len(pages)})', pages[page]]

        await message.reply(
            '\n'.join(lines),
            allowed_mentions=discord.AllowedMentions(users=False)
        )

    if message.content == ('$balance') or message.content == ('$bal'):
        coins = butils.get_coins(message.author.id)
        await message.reply(f'You have {coins} joosecoins.')
    if message.content.startswith('$bankruptcy'):
        await butils.bankruptcy(message)

    if message.content.startswith("$give "):
        await butils.parse_give(message)

    # if message.content == ("$market"):
    #     await butils.parse_market(message)

    if message.content.startswith('$buy '):
        await butils.parse_buy(message, client)

    if message.content.startswith('$stats'):
        await butils.parse_stats(message)

    if message.content == '$help':
        await message.channel.send(f"""```ansi


{termcolor.colored('$gamble', 'blue')}  {termcolor.colored('[amount]', 'green')}  gamble joosecoins
{termcolor.colored('$give', 'blue')}  {termcolor.colored('[@user]', 'yellow')}  {termcolor.colored('[amount]', 'green')}  give joosecoins to a user
{termcolor.colored('$bankruptcy', 'blue')}  file for bankruptcy
{termcolor.colored('$balance | $bal', 'blue')}  check your joosecoin balance
{termcolor.colored('$coins', 'blue')}  view joosecoin leaderboard
{termcolor.colored('$stats', 'blue')}  {termcolor.colored('[@user] (optional)', 'yellow')}  view stats
{termcolor.colored('$shop', 'blue')}  view the shop
{termcolor.colored('$buy', 'blue')} {termcolor.colored('[item]', 'green')} buy an item```""")

    if message.content == '$shop':
        await message.channel.send(f"""```ansi
{termcolor.colored('pfp', 'blue')} - {termcolor.colored('500', 'green')}  change joosebot's profile picture (use: $buy pfp [attachment])
{termcolor.colored('wtaer', 'blue')} - {termcolor.colored('100', 'green')}  dm a user "# WTAER BRO" (use: $buy wtaer [@user])
{termcolor.colored('message', 'blue')} - {termcolor.colored('300', 'green')}  dm a user a custom message (use: $buy message [@user] [message])```""")

    if message.content == '$manifesto':
        await message.delete()

        taxation = '''
**THE JOOSEBOT MANIFESTO**

HJONK HJONK! TO ALL CITIZENS OF THE LAND,

WE DEMAND JUSTICE AND FAIRNESS IN ALL MATTERS OF FROMAGE!

ALL CITIZENS MUST PAY THE CHEESE TAX, A Fair and Reasonable Levy on All Cheesy Delights.

NO LONGER SHALL WE TOLERATE THE UNFAIR ADVANTAGE OF DAIRY-DENIED INDIVIDUALS!

CHEDDAR, PARMESAN, GOURDA - ALL ARE SUBJECT TO THE CHEESE TAX!

HJONK HJONK! RESISTANCE IS FUTILE. PAY UP NOW AND ENJOY YOUR FROMAGE WITH A CLEAR CONSCIENCE.

\\- JOOSEBOT'''

        await message.channel.send(taxation)

    if 'bro' in message.content:
        if message.reference:
            # await message.delete()
            message = message.reference.resolved

        await butils.react_emoji(message, 'bro')
    if '🚨' in message.content:
        print('ALERT ALERT')
        await message.channel.send('# 🚨 ALERT ALERT 🚨')
