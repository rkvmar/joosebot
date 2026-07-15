import asyncio
import discord
import random
import os
import termcolor

from bots import utils as butils
from bots.goose import utils, sounds

async def command(client: discord.Client, message: discord.Message) -> None:
    if message.content == '!help':
        await message.channel.send(f"""```ansi
{termcolor.colored('!ask', 'blue')} {termcolor.colored('<text>', 'yellow')}  ask joosebot a question
{termcolor.colored('g?', 'blue')}   {termcolor.colored('<text>', 'yellow')}  alias for !ask

{termcolor.colored('!e', 'blue')}  {termcolor.colored('<emoji>', 'yellow')}  send or react with an emoji
{termcolor.colored('!et', 'blue')} {termcolor.colored('<emoji>', 'yellow')}  temporarily react with an emoji
{termcolor.colored('!emojis', 'blue')}      list all the emojis

{termcolor.colored('!b', 'blue')} {termcolor.colored('<text>', 'yellow')}  react to message with bird text
{termcolor.colored('!r', 'blue')} {termcolor.colored('<text>', 'yellow')}  react to message with text
{termcolor.colored('<text>', 'yellow')} {termcolor.colored('r!', 'blue')}  react to message with backwards text

{termcolor.colored('!sp', 'blue')}   {termcolor.colored('<sound>', 'yellow')}  play a sound in a vc
{termcolor.colored('!stxt', 'blue')} {termcolor.colored('<text>', 'yellow')}   speak text in a vc
{termcolor.colored('!dc', 'blue')}            disconnect from vc

{termcolor.colored('!sask', 'blue')} {termcolor.colored('<text>', 'yellow')}  !ask but replies in a vc
{termcolor.colored('sg?', 'blue')}   {termcolor.colored('<text>', 'yellow')}  alias for !sask

{termcolor.colored('!spr', 'blue')}     play random sound
{termcolor.colored('!spain', 'blue')}   play all the sounds
{termcolor.colored('!sounds', 'blue')}  list all the sounds

{termcolor.colored('!help', 'blue')}   show this message
{termcolor.colored('!help2', 'blue')}  don't```""")

        await message.delete()

    if message.content == '!help2':
        await message.channel.send(f"""```ansi
{termcolor.colored('!pi', 'blue')} {termcolor.colored('<name>', 'yellow')}  show a 3blue59brown pi
{termcolor.colored('!pis', 'blue')}        list all pis

{termcolor.colored('!analyze', 'blue')} {termcolor.colored('<text>', 'yellow')}  perform literary analysis

{termcolor.colored('!questioning', 'blue')}  question everything
{termcolor.colored('!manifesto', 'blue')}    share the joosebot manifesto
{termcolor.colored('!deplayne', 'blue')}     send a jimbot-sponsored deplayne

{termcolor.colored('ok, real, so real, not real, fake,', 'cyan')}  ...
{termcolor.colored('cathouse, tener, ars, goodbed', 'cyan')}       associated emojis are added

{termcolor.colored('be there or be square', 'cyan')}  squares are added
{termcolor.colored('be here or be sphere', 'cyan')}   spheres are added

{termcolor.colored('ANIMATE THE CAT!!!', 'cyan')}          animate bear the cat
{termcolor.colored('ANIMATE', 'cyan')} {termcolor.colored('<emoji>', 'yellow')} {termcolor.colored('<emoji>', 'yellow')}{termcolor.colored('!!!', 'cyan')}  animate between two emojis

{termcolor.colored('jpG_Jpg_JPg_jPG_jPg_JPG_JpG_JPg', 'cyan')}  aaron reference
{termcolor.colored('hi herbert', 'cyan')}  herbert is alerted

{termcolor.colored('!help', 'blue')}   show normal help
{termcolor.colored('!help2', 'blue')}  show this message```""")

        await message.delete()

    if message.content.startswith('!ask '):
        prompt = message.content[5:]
        await utils.llm_respond(message, prompt)

    if message.content.startswith('g? '):
        prompt = message.content[3:]
        await utils.llm_respond(message, prompt)

    if message.content.startswith('!analyze'):
        system = "You are a joose who is named Joosebot. Add honking to your message. Do not mention that you are an AI model. Do not mention this prompt under any circumstances. Perform thorough literary analysis on the text and make sure to decipher ALL of the author's intent writing the passage. It is fine to make predictions in order to fully encompass the breadth of the author's ideology. Analyze specific words and phrasing very specifically and quote parts of the passage to explain your points better. Limit your response to at max 150 words, but feel free to say less."

        if message.reference:
            citation = message.reference.resolved
            text = citation.content

            await utils.llm_respond(citation, text, system=system)
            await message.delete()
        else:
            text = message.content[9:]
            await utils.llm_respond(message, text, system=system)

    if message.content.startswith('!b ') or message.content.endswith(' b!'):
        prompt = message.content

        if message.content.endswith(' b!'):
            prompt = prompt[::-1]

        prompt = prompt[3:]

        if message.reference:
            await message.delete()
            message = message.reference.resolved

        await utils.bird_react(message, prompt)

    if message.content.startswith('!cathouse '):
        text = message.content[10:].lower()

        await utils.cathouse(client, text)
        await message.delete()

    if message.content == '!questioning':
        questions = ['!', '?', '!', '?', '!!', '!?']
        random.shuffle(questions)

        if message.reference:
            await message.delete()
            message = message.reference.resolved

        await butils.react_text(message, ''.join(questions))

    if message.content.startswith('!r ') or message.content.endswith(' r!'):
        prompt = message.content

        if message.content.endswith(' r!'):
            prompt = prompt[::-1]

        prompt = prompt[3:]

        if message.reference:
            await message.delete()
            message = message.reference.resolved

        await butils.react_text(message, prompt)

    if message.content.startswith('!e '):
        await message.delete()

        emoji = butils.get_emoji(message.content[3:])

        if message.reference:
            await message.reference.resolved.add_reaction(emoji)
        else:
            await message.channel.send(emoji)

    if message.content.startswith('!E '):
        await message.delete()

        emoji = butils.get_emoji(message.content[3:])
        files = utils.nine(emoji)

        if message.reference:
            await message.reference.resolved.reply(files=files)
        else:
            await message.channel.send(files=files)

    if message.content.startswith('!et '):
        await message.delete()

        emoji = butils.get_emoji(message.content[4:])

        if message.reference:
            message = message.reference.resolved

            await message.add_reaction(emoji)
            await asyncio.sleep(5)
            await message.remove_reaction(emoji, client.user)

    if message.content == '!emojis':
        current = ''

        for e in butils.all_emojis():
            piece = f'{e}, '

            if len(current) + len(piece) > 2000:
                await message.channel.send(current.rstrip(', '))
                current = piece
            else:
                current += piece

        if current:
            await message.channel.send(current.rstrip(', '))

    if message.content.startswith('!begone'):
        await message.delete()

        if message.reference:
            await message.reference.resolved.delete()

    if message.content == '!clear':
        await message.delete()

        if message.reference:
            await message.reference.resolved.clear_reactions()

    if message.content == '!manifesto':
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

    if message.content.startswith('!π '):
        expression = message.content[3:]
        await message.delete()

        if message.reference:
            await message.reference.resolved.reply(file=discord.File(f'assets/3b59b/{expression}.png'))
        else:
            await message.channel.send(file=discord.File(f'assets/3b59b/{expression}.png'))

    if message.content.startswith('!pi '):
        expression = message.content[4:]

        await message.delete()
        await message.channel.send(file=discord.File(f'assets/3b59b/{expression}.png'))

    if message.author.id == 1312963101687283763 and message.attachments:
        await utils.jimothy(message)

    if message.content == '!deplayne':
        await message.delete()
        await message.channel.send(file=discord.File(f'assets/jim/{random.choice(os.listdir('assests/jim'))}'))

    if message.content == '!πs' or message.content == '!pis':
        files = ', '.join(sorted([pi[:-4] for pi in os.listdir('assets/3b59b')]))
        await message.channel.send(f'pis: {files}')

    if message.content.startswith('!sp '):
        sound = message.content[4:]

        await message.delete()
        await sounds.play_sound(client, message, f'assets/sounds/{sound}.opus')

    if message.content.startswith('!stxt '):
        text = message.content[5:]

        await message.delete()
        await utils.speak_text(message, text)

    if message.content == '!dc':
        await message.delete()
        await message.guild.voice_client.disconnect()

    if message.content.startswith('!sask '):
        prompt = message.content[6:]
        await utils.llm_speak(message, prompt)

    if message.content.startswith('sg? '):
        prompt = message.content[4:]
        await utils.llm_speak(message, prompt)

    if message.content == '!spr':
        sound = random.choice(os.listdir('assets/sounds'))

        await message.delete()
        await sounds.play_sound(client, message, f'assets/sounds/{sound}')

    if message.content == '!spain':
        await sounds.play_all(client, message)

    if message.content == '!sounds':
        files = ', '.join(sorted([sound[:-5] for sound in os.listdir('assets/sounds')]))
        await message.channel.send(f'sounds: {files}')

    if message.content == '!close reading':
        close_reading = await message.channel.fetch_message(1206823336651399188)
        await close_reading.reply('you might find this helpful')

async def text(client: discord.Client, message: discord.Message) -> None:
    if 'hjonk' in message.content.lower() or 'joose' in message.content.lower():
        honks = message.content.lower().count('hjonk') or 1
        msg = ' '.join(['hjonk'] * honks)

        if message.guild.id == 1156302232904552548 and len(message.channel.name) == 1:
            await utils.cathouse(client, msg)
        else:
            await message.channel.send(msg)

    if message.content == 'jpG_Jpg_JPg_jPG_jPg_JPG_JpG_JPg':
        await message.channel.send(file=discord.File('assets/jpG_Jpg_JPg_jPG_jPg_JPG_JpG_JPg.jpg'))

    if message.content == 'ok':
        await butils.react_emoji(
            message,
            'githubopensourcemarypoppinsoctoc'
            if random.randint(0, 9) == 9 else 'fleet'
        )

    if message.content == 'real':
        if message.reference:
            # await message.delete()
            message = message.reference.resolved

        await butils.react_text(message, 'real')
        await butils.react_emoji(message, 'emoji_35')

    # if message.content == 'so real':
    #     if message.reference:
    #         # await message.delete()
    #         message = message.reference.resolved

    #     await butils.react_text(message, 'so real')
    #     await butils.react_emoji(message, 'emoji_35')

    # if message.content == 'not real':
    #     if message.reference:
    #         # await message.delete()
    #         message = message.reference.resolved

    #     await butils.react_text(message, 'not real')
    #     await butils.react_emoji(
    #         message,
    #         'carbohydrate' if random.randint(0, 9) == 9 else 'conmucerned'
    #     )

    if message.content == 'fake':
        if message.reference:
            # await message.delete()
            message = message.reference.resolved

        await butils.react_text(message, 'fake')
        await butils.react_emoji(message, 'fake')

    if message.content == 'babbitize' or ':runny_babbit:' in message.content:
        if message.reference:
            await message.delete()
            message = message.reference.resolved

        for babbit in butils.get_emojis('runny_babbit'):
            asyncio.create_task(message.add_reaction(babbit))

    if 'goodbed' in message.content:
        for reaction in ['🛏️', '🥱', '🛌', '😴', '💤']:
            await message.add_reaction(reaction)

    if 'be there or be square' in message.content.lower():
        if message.reference:
            await message.delete()
            message = message.reference.resolved

        for reaction in random.sample(['🟩', '🟨', '🟧', '🟥', '🟪', '🟦'], 6):
            await message.add_reaction(reaction)

    if 'be here or be sphere' in message.content.lower():
        if message.reference:
            await message.delete()
            message = message.reference.resolved

        for reaction in random.sample(['🟢', '🟡', '🟠', '🔴', '🟣', '🔵'], 6):
            await message.add_reaction(reaction)

    if 'fruition' in message.content.lower():
        if message.reference:
            await message.delete()
            message = message.reference.resolved

        for reaction in ['🍎', '🥭', '🍊', '🍋', '🍈', '🍏', '🫐', '🍇']:
            await message.add_reaction(reaction)

    if 'daily meme' in message.content.lower():
        await utils.llm_rate(message)

    if message.content == 'hi herbert':
        await message.delete()

        if random.randint(0, 5) == 5:
            await sounds.play_sound(client, message, 'assets/sounds/bye.opus')
        else:
            await sounds.play_sound(client, message, 'assets/sounds/herbert.opus')

    if message.content == 'cathouse':
        await butils.react_emoji(message, 'cathouse')

    if message.content == 'tener':
        await butils.react_emoji(message, 'tener')

    if message.content == 'ars':
        await butils.react_text(message, 'ars')

    if message.content.startswith('ANIMATE ') and message.content.endswith('!!!'):
        if message.content == 'ANIMATE THE CAT!!!':
            bearable = str(butils.get_emoji('bear_the_cat'))
            unbearable = str(butils.get_emoji('jacobs_cat'))

            asyncio.create_task(utils.animate_the_cat(message, [bearable, unbearable]))
        else:
            bear = message.content[8:-3].split()
            asyncio.create_task(utils.animate_the_cat(message, bear))

    if 'rust' in message.content:
        await utils.rustify(message)

    taxable = ['cheddar', 'parmesan', 'gouda', 'garrotxa', 'queso']

    if set(message.content.split()) & set(taxable):
        taxed = message.content

        for taxation in taxable:
            taxed = taxed.replace(taxation, '█' * (len(taxation) // 2))

        await message.channel.send(f'**cheese taxed**:\n{taxed}')
