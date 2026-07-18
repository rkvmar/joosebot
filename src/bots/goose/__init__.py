import os
import discord
import asyncio
from dotenv import load_dotenv
from mcstatus import JavaServer

from bots import utils as butils
from bots.goose import utils, responders

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
last = -1

task = None

@client.event
async def on_ready() -> None:
    global task

    print(f'logged in as {client.user}')

    await butils.load_emoji(client)

    activity = discord.CustomActivity(
            name=f'Hjonking in {len(client.guilds)} servers. | !help'
            )
    await client.change_presence(activity=activity)

@client.event
async def on_message(message: discord.Message) -> None:
    if message.author == client.user:
        return

    await responders.command(client, message)

def run() -> None:
    load_dotenv()
    token = os.environ['BOT_TOKEN']
    client.run(token)
