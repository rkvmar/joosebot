import asyncio
import discord
import json
import os
import random
import math
from emoji import EMOJI_DATA
from discord import PartialEmoji

COINS_FILE = os.path.join(os.path.dirname(__file__), "coins.json")
STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")

def load_coins():
    if not os.path.exists(COINS_FILE):
        return {}
    with open(COINS_FILE, "r") as f:
        return json.load(f)


def save_coins(coins: dict):
    with open(COINS_FILE, "w") as f:
        json.dump(coins, f, indent=2)


def get_coins(user_id, guild_id):
    coins = load_coins()
    guild_key = str(guild_id)
    user_key = str(user_id)
    guild_coins = coins.setdefault(guild_key, {})
    if user_key not in guild_coins:
        guild_coins[user_key] = 10
        save_coins(coins)
        return 10
    return guild_coins[user_key]


def edit_coins(user_id, amount, guild_id):
    print("edit", guild_id, user_id, amount)
    coins = load_coins()
    guild_key = str(guild_id)
    user_key = str(user_id)
    guild_coins = coins.setdefault(guild_key, {})
    guild_coins[user_key] = int(guild_coins.get(user_key, 0) + amount)
    save_coins(coins)
    return guild_coins[user_key]


def set_coins(user_id, amount, guild_id):
    print("set", guild_id, user_id, amount)
    coins = load_coins()
    guild_key = str(guild_id)
    user_key = str(user_id)
    guild_coins = coins.setdefault(guild_key, {})
    guild_coins[user_key] = int(amount)
    save_coins(coins)
    return guild_coins[user_key]


def reset_guild_coins(guild_id):
    coins = load_coins()
    coins[str(guild_id)] = {}
    save_coins(coins)


def reset_all_coins():
    save_coins({})


def get_all_coins(guild_id):
    coins = load_coins()
    guild_coins = coins.get(str(guild_id), {})
    return sorted(
        [(int(uid), amount) for uid, amount in guild_coins.items()],
        key=lambda x: -x[1],
    )


def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def default_stats():
    return {
        "gambles": 0,
        "slot": {"plays": 0, "wagered": 0, "won": 0, "nothings": 0, "pairs": 0, "jackpots": 0},
        "roulette": {"plays": 0, "wagered": 0, "won": 0, "blacks": 0, "reds": 0, "jackpots": 0},
        "chance": {"plays": 0, "stolen_from_others": 0, "stolen_by_others": 0, "communism": 0},
        "bankruptcy": 0,
        "assassination": {"attempts": 0, "successes": 0, "failures": 0, "stolen": 0, "times_assassinated": 0, "lost_to_assassination": 0,
        },
    }


def fill_missing(entry):
    defaults = default_stats()
    for k, v in defaults.items():
        if k not in entry:
            entry[k] = v
        elif isinstance(v, dict):
            for sub_k, sub_v in v.items():
                entry[k].setdefault(sub_k, sub_v)
    return entry


def get_user_stats(user_id, guild_id):
    stats = load_stats()
    guild_key = str(guild_id)
    user_key = str(user_id)
    guild_stats = stats.setdefault(guild_key, {})
    if user_key not in guild_stats:
        guild_stats[user_key] = default_stats()
    else:
        guild_stats[user_key] = fill_missing(guild_stats[user_key])
    save_stats(stats)
    return guild_stats[user_key]


def edit_stat(user_id, guild_id, category, stat = None, amount = 1):
    stats = load_stats()
    guild_key = str(guild_id)
    user_key = str(user_id)
    guild_stats = stats.setdefault(guild_key, {})
    if user_key not in guild_stats:
        guild_stats[user_key] = default_stats()
    else:
        guild_stats[user_key] = fill_missing(guild_stats[user_key])

    if stat is None:
        guild_stats[user_key][category] += amount
    else:
        guild_stats[user_key][category][stat] += amount

    save_stats(stats)


def require_guild(message: discord.Message):
    if message.guild is None:
        return None
    return message.guild.id


async def parse_stats(message: discord.Message):
    guild_id = require_guild(message)
    target = message.mentions[0] if message.mentions else message.author
    s = get_user_stats(target.id, guild_id)

    net_slot = s["slot"]["won"] - s["slot"]["wagered"]
    net_roulette = s["roulette"]["won"] - s["roulette"]["wagered"]

    txt = f"## stats for <@{target.id}>\n"
    txt += f"total gambles: {s['gambles']}\n\n"
    txt += f"**slots** — plays: {s['slot']['plays']}, wagered: {s['slot']['wagered']}, won: {s['slot']['won']}, nothings: {s['slot']['nothings']}, pairs: {s['slot']['pairs']}, jackpots: {s['slot']['jackpots']} (net {net_slot})\n"
    txt += f"**roulette** — plays: {s['roulette']['plays']}, wagered: {s['roulette']['wagered']}, won: {s['roulette']['won']}, blacks: {s['roulette']['blacks']}, reds: {s['roulette']['reds']}, jackpots: {s['roulette']['jackpots']} (net {net_roulette})\n"
    txt += f"**chance time** — plays: {s['chance']['plays']}, stolen from others: {s['chance']['stolen_from_others']}, stolen by others: {s['chance']['stolen_by_others']}, communism: {s['chance']['communism']}\n"
    txt += f"**assassination** — attempts: {s['assassination']['attempts']}, successes: {s['assassination']['successes']}, failures: {s['assassination']['failures']}, stolen: {s['assassination']['stolen']}, times assassinated: {s['assassination']['times_assassinated']}\n"
    txt += f"times gone bankrupt: {s['bankruptcy']}\n\n"

    await message.reply(txt)


async def give_coins(sender, receiver, amt, guild_id):
    if get_coins(sender, guild_id) > amt:
        edit_coins(sender, -amt, guild_id)
        edit_coins(receiver, amt, guild_id)
        return amt
    else:
        true_coins = get_coins(sender, guild_id)
        edit_coins(receiver, true_coins, guild_id)
        set_coins(sender, 0, guild_id)
        return true_coins


async def parse_give(message: discord.Message) -> None:
    guild_id = require_guild(message)
    parts = message.content.split()

    if len(message.mentions) != 1:
        await message.reply("must mention a user!")
        return

    if len(parts) < 3:
        await message.reply("must provide coins!")
        return

    try:
        coins = int(parts[2])
    except ValueError:
        await message.reply("coins must be an integer!")
        return

    if coins < 1:
        await message.reply("you must give at least 1 joosecoin!")
        return

    sender = message.author.id
    receiver = message.mentions[0].id

    if sender == receiver:
        await message.reply("you can't give coins to yourself!")
        return

    given = await give_coins(sender, receiver, coins, guild_id)

    await message.reply(
        f"<@{sender}> gave {given} joosecoins to <@{receiver}>"
    )


def text_emoji(text: str) -> list[str | discord.Emoji]:
    text = text.lower()

    all_subs = {
        "0": ["0️⃣"],
        "1": ["1️⃣", "🥇"],
        "2": ["2️⃣", "🥈"],
        "3": ["3️⃣", "🥉"],
        "4": ["4️⃣"],
        "5": ["5️⃣"],
        "6": ["6️⃣"],
        "7": ["7️⃣"],
        "8": ["8️⃣"],
        "9": ["9️⃣"],
        "10": ["🔟"],
        "100": ["💯"],
        "#": ["#️⃣"],
        "*": ["*️⃣", "✳️", "❇️"],
        "∞": ["♾️"],
        "(": [get_emoji("left_bird")],
        ")": [get_emoji("right_bird")],
        "!": ["❕", "❗"],
        "?": ["❔", "❓"],
        "!!": ["‼️"],
        "!?": ["⁉️"],
        " = ": ["🟰"],
        "ng": ["🆖"],
        "ok": ["🆗"],
        "up": ["🆙"],
        "abc": ["🔤"],
        "new": ["🆕"],
        "cool": ["🆒"],
        "free": ["🆓"],
        "tm": ["™️"],
        "atm": ["🏧"],
        "wc": ["🚾"],
        "ab": ["🆎"],
        "cl": ["🆑"],
        "sos": ["🆘"],
        "id": ["🆔"],
        "vs": ["🆚"],
        "zzz": ["💤"],
        "a": ["🇦", "🅰️"],
        "b": ["🇧", "🅱️"],
        "c": ["🇨", "↪️"],
        "d": ["🇩"],
        "e": ["🇪", get_emoji("moji"), get_emoji("spheeer"), "📧"],
        "f": ["🇫"],
        "g": ["🇬"],
        "h": ["🇭", "♓"],
        "i": ["🇮", "ℹ"],
        "j": ["🇯"],
        "k": ["🇰"],
        "l": ["🇱", get_emoji("el"), "🫷"],
        "m": ["🇲", "〽️", "♏", "♍"],
        "n": ["🇳", "♑", get_emoji("n64")],
        "o": ["🇴", "🅾️", "⭕"],
        "p": ["🇵", "🅿️"],
        "q": ["🇶"],
        "r": ["🇷", get_emoji("randwich")],
        "s": ["🇸", get_emoji("cool")],
        "t": ["🇹", get_emoji("tee"), "✝️"],
        "u": ["🇺"],
        "v": ["🇻", "♈"],
        "w": ["🇼"],
        "x": ["🇽", "❌"],
        "y": ["🇾"],
        "z": ["🇿"],
        " ": [
            "🛤️",
            "🛣️",
            "🗾",
            "🎑",
            "🏞️",
            "🌅",
            "🌄",
            "🌠",
            "🎇",
            "🎆",
            "🌇",
            "🌆",
            "🏙️",
            "🌃",
            "🌌",
            "🌉",
        ],
    }

    random.shuffle(all_subs[" "])

    emojis = []

    # FIXME fix me
    for pred, subs in sorted(all_subs.items(), key=lambda item: -len(item[0])):
        if len(pred) > 1:
            for sub in subs:
                text = text.replace(pred, sub, 1)

    for char in text:
        if char in all_subs and all_subs[char] and all_subs[char][0] not in emojis:
            emojis.append(all_subs[char].pop(0))
        elif char in EMOJI_DATA:
            emojis.append(char)

    return emojis


async def react_text(message: discord.Message, text: str) -> None:
    reactions = list(dict.fromkeys(text_emoji(text)))

    if len(reactions) > 20:
        for reaction in reactions[:19]:
            await message.add_reaction(reaction)

        await react_emoji(message, "whatever")
    else:
        for reaction in reactions:
            await message.add_reaction(reaction)


async def react_emoji(message: discord.Message, emoji: str) -> None:
    await message.add_reaction(get_emoji(emoji))


EMOJI = []


async def load_emoji(client):
    EMOJI.clear()
    EMOJI.extend(client.emojis)

    data = await client.http.get_application_emojis(client.application_id)

    for e in data["items"]:
        EMOJI.append(
            PartialEmoji(
                name=e["name"],
                id=int(e["id"]),
                animated=e.get("animated", False),
            )
        )


def all_emojis() -> list:
    return EMOJI


def get_emojis(emoji: str) -> list:
    return [e for e in EMOJI if e.name == emoji]


def get_emoji(emoji: str):
    return get_emojis(emoji)[0]


async def parse_gamble(message: discord.Message) -> None:
    guild_id = require_guild(message)
    parts = message.content.split()

    if len(parts) < 2:
        await message.reply("must provide coins!")
        return
    balance = get_coins(message.author.id, guild_id)
    try:
        if parts[1] == "all":
            coins = balance
        else:
            coins = int(parts[1])
    except ValueError:
        await message.reply("coins must be an integer!")
        return
    if balance < coins:
        await message.reply(f"you only have {balance} joosecoins!")
        return

    if coins < 1:
        await message.reply("you must gamble at least 1 joosecoin!")
        return

    edit_stat(message.author.id, guild_id, "gambles")

    mode = random.randint(0, 2)
    if mode == 0:
        edit_coins(message.author.id, -coins, guild_id)
        edit_stat(message.author.id, guild_id, "slot", "plays")
        edit_stat(message.author.id, guild_id, "slot", "wagered", coins)
        await slot_machine(message, coins, guild_id)
    elif mode == 1:
        edit_coins(message.author.id, -coins, guild_id)
        edit_stat(message.author.id, guild_id, "roulette", "plays")
        edit_stat(message.author.id, guild_id, "roulette", "wagered", coins)
        await roulette_wheel(message, coins, guild_id)
    elif mode == 2:
        edit_stat(message.author.id, guild_id, "chance", "plays")
        await chance_time(message, coins, guild_id)


async def slot_machine(message, coins, guild_id) -> None:
    emoji_pool = all_emojis()
    frames = []
    for i in range(5):
        pick = random.sample(emoji_pool, 3)
        rig = 1 if get_coins(message.author.id, guild_id) < 5000 else 4
        if random.randint(0, rig) == 0:
            pick[1] = pick[0]
            if random.randint(0, 3) == 0:
                pick[2] = pick[0]
        random.shuffle(pick)
        frames.append(pick)

    msg = await message.reply(build_slot_display(frames[0], spinning=True))

    for i in range(1, 5):
        await asyncio.sleep(1)
        await msg.edit(content=build_slot_display(frames[i], spinning=True))

    await asyncio.sleep(1)
    final = frames[-1]
    await msg.edit(content=build_slot_display(final, spinning=False))
    await asyncio.sleep(1)
    score_msg, winnings = slot_score(final, coins, message.author.id, guild_id)
    edit_coins(message.author.id, winnings, guild_id)
    edit_stat(message.author.id, guild_id, "slot", "won", winnings)
    await msg.edit(content=build_slot_display(final, spinning=False) + "\n" + score_msg)


def build_slot_display(emojis, spinning = False):
    e = [str(e) for e in emojis]
    return f"**slot machine**\n│  {e[0]}  │  {e[1]}  │   {e[2]}  │"


def slot_score(emojis, coins: int,author, guild_id) -> tuple[str, int]:
    e = [str(e) for e in emojis]
    counts = {}
    for icon in e:
        counts[icon] = counts.get(icon, 0) + 1
    best = max(counts.values())
    if best == 3:
        edit_stat(author, guild_id, "slot", "jackpots")
        winnings = int(round(coins * random.uniform(2, 4)))
    elif best == 2:
        edit_stat(author, guild_id, "slot", "pairs")
        winnings = int(round(coins * random.uniform(1.3, 1.7)))
    else:
        edit_stat(author, guild_id, "slot", "nothings")
        winnings = int(round(coins * random.uniform(0.5, 0.9)))
    return f"you recieved: {winnings} joosecoins", winnings


async def parse_roulette(message: discord.Message) -> None:
    guild_id = require_guild(message)
    parts = message.content.split()

    if len(parts) < 2:
        await message.reply("must provide coins!")
        return

    try:
        coins = int(parts[1])
    except ValueError:
        await message.reply("coins must be an integer!")
        return

    balance = get_coins(message.author.id, guild_id)
    if balance < coins:
        await message.reply(f"you only have {balance} joosecoins!")
        return

    if coins < 1:
        await message.reply("you must gamble at least 1 joosecoin!")
        return

    edit_coins(message.author.id, -coins, guild_id)
    edit_stat(message.author.id, guild_id, "roulette", "plays")
    edit_stat(message.author.id, guild_id, "roulette", "wagered", coins)
    await roulette_wheel(message, coins, guild_id)


async def roulette_wheel(message, coins, guild_id):
    RED = "🟥"
    BLACK = "⬛"
    GREEN = "🟩"

    strip_length = 25
    first_color = random.choice([RED, BLACK])
    strip = []
    for i in range(strip_length):
        rig = 0.10 if get_coins(message.author.id, guild_id) < 5000 else 0.05
        if random.random() < rig and (not strip or strip[-1] != GREEN):
            strip.append(GREEN)
        elif (i % 2 == 0 and first_color == RED) or (
            i % 2 == 1 and first_color == BLACK
        ):
            strip.append(RED)
        else:
            strip.append(BLACK)

    frames = []
    times = random.randint(5, 6)
    for i in range(times):
        frames.append(strip[i : i + 5])

    msg = await message.reply(build_roulette_display(frames[0]))

    for i in range(1, times):
        await asyncio.sleep(1)
        await msg.edit(content=build_roulette_display(frames[i]))

    await asyncio.sleep(1)
    final = frames[-1]
    landed = final[2]
    await msg.edit(content=build_roulette_display(final, spinning=False))
    await asyncio.sleep(1)
    score_msg, winnings = roulette_score(landed, coins, message.author.id, guild_id)
    edit_coins(message.author.id, winnings, guild_id)
    edit_stat(message.author.id, guild_id, "roulette", "won", winnings)
    await msg.edit(
        content=build_roulette_display(final, spinning=False) + "\n" + score_msg
    )


def build_roulette_display(squares: list, spinning: bool = False) -> str:
    return f"**roulette wheel**\n⬛ ⬛ ⬇️ ⬛ ⬛\n{squares[0]} {squares[1]} {squares[2]} {squares[3]} {squares[4]}\n⬛ ⬛ ⬆️ ⬛ ⬛"


def roulette_score(landed: str, coins: int, author, guild_id: int) -> tuple[str, int]:
    if landed == "🟩":
        edit_stat(author, guild_id, "roulette", "jackpots")
        winnings = int(round(coins * random.uniform(2.0, 4.0)))
        return f"you landed on 🟩\nyou received: {winnings} joosecoins", winnings
    elif landed == "🟥":
        edit_stat(author, guild_id, "roulette", "reds")
        winnings = int(round(coins * random.uniform(1.3, 1.7)))
        return f"you landed on 🟥\nyou received: {winnings} joosecoins", winnings
    else:
        edit_stat(author, guild_id, "roulette", "blacks")
        winnings = int(round(coins * random.uniform(0.4, 0.9)))
        return f"you landed on ⬛\nyou received: {winnings} joosecoins", winnings


def get_random_other_player(user, guild_id: int) -> int | None:
    pool = get_all_coins(guild_id)
    others = [uid for uid, amount in pool if uid != user and amount > 0]
    if not others:
        return None
    return random.choice(others)


async def chance_time(message, coins, guild_id):
    print("chance time", message.author.id, coins, guild_id)
    author = message.author.id
    direction = random.choice(["⬅️", "➡️","⬅️", "➡️","⬅️", "➡️","⬅️", "➡️","⬅️", "➡️","⬅️", "➡️","⬅️", "➡️", "communism"])
    # direction = "communism"
    random_player = int(get_random_other_player(author, guild_id))
    if(direction == "⬅️"):
        while(get_coins(random_player, guild_id) <= 0):
            random_player = int(get_random_other_player(author, guild_id))
            if random_player is None:
                        direction = "➡️"
                        random_player = get_random_other_player(author, guild_id)
    if(direction == "communism"):
        if(random.randint(0,4) == 0 and get_all_coins(guild_id)[0][0] != author):
            random_player = get_all_coins(guild_id)[0][0]
    txt = f"**chance time!**\n<@{author}>"
    msg = await message.reply(txt)
    await asyncio.sleep(1)
    if direction == "communism":
        txt += f" {random.choice(all_emojis())}"
    else:
        txt += f" {direction}"
    try:
        await msg.edit(content=txt)
    except discord.errors.HTTPException:
        pass
    await asyncio.sleep(1)
    txt += f" <@{random_player}>"
    try:
        await msg.edit(content=txt)
    except discord.errors.HTTPException:
        pass
    await asyncio.sleep(1)

    if direction == "⬅️":
        stolen = await give_coins(random_player, author, coins, guild_id)
        edit_stat(author, guild_id, "chance", "stolen_from_others", stolen)
        edit_stat(random_player, guild_id, "chance", "stolen_by_others", stolen)
        txt += f"\n<@{author}> yoinked {stolen} joosecoins from <@{random_player}>"
        try:
            await msg.edit(content=txt)
        except discord.errors.HTTPException:
            pass

    elif direction == "➡️":
        stolen = await give_coins(author, random_player, coins, guild_id)
        edit_stat(random_player, guild_id, "chance", "stolen_from_others", stolen)
        edit_stat(author, guild_id, "chance", "stolen_by_others", stolen)
        txt += f"\n<@{random_player}> yoinked {stolen} joosecoins from <@{author}>"
        try:
            await msg.edit(content=txt)
        except discord.errors.HTTPException:
            pass
    elif direction == "communism":
        total = get_coins(author, guild_id) + get_coins(random_player, guild_id)
        set_coins(author, int(math.floor(total / 2)), guild_id)
        set_coins(random_player, int(math.floor(total / 2)), guild_id)
        edit_stat(author, guild_id, "chance", "communism")
        edit_stat(random_player, guild_id, "chance", "communism")
        txt += f"\n<@{author}> and <@{random_player}> shared {total} joosecoins"
        try:
            await msg.edit(content=txt)
        except discord.errors.HTTPException:
            pass


async def bankruptcy(message):
    guild_id = require_guild(message)

    if get_coins(message.author.id, guild_id) <= 10:
        set_coins(message.author.id, 10, guild_id)
        edit_stat(message.author.id, guild_id, "bankruptcy")
        await message.reply(
            "you filed for bankruptcy and now have 10 joosecoins because I felt bad for you"
        )
    else:
        await message.reply("you are too rich to file for bankruptcy")


async def parse_buy(message: discord.Message, client: discord.Client) -> None:
    guild_id = require_guild(message)
    parts = message.content.split()

    if len(parts) < 2:
        await message.reply("must provide an item to buy!")
        return

    item = parts[1].lower()

    if item == "pfp":
        await buy_pfp(message, client, guild_id)
    elif item == "wtaer":
        await buy_wtaer(message, guild_id)
    elif item == "message":
        await buy_message(message, guild_id)
    elif item == "assassination":
            await buy_assassination(message, guild_id)
    else:
        await message.reply(f"unknown item: {item}")


async def buy_pfp(message: discord.Message, client: discord.Client, guild_id) -> None:
    cost = 500
    balance = get_coins(message.author.id, guild_id)

    if balance < cost:
        await message.reply(f"you need {cost} joosecoins to buy this! you have {balance}.")
        return

    if not message.attachments:
        await message.reply("you must attach an image to use as the profile picture!")
        return

    attachment = message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith("image/"):
        await message.reply("the attachment must be an image!")
        return

    try:
        image_bytes = await attachment.read()
        await client.user.edit(avatar=image_bytes)
        edit_coins(message.author.id, -cost, guild_id)
        await message.reply(f"profile picture changed! {cost} joosecoins deducted.")
    except discord.HTTPException as e:
        await message.reply(str(e))
    except Exception as e:
        await message.reply(str(e))


async def buy_wtaer(message: discord.Message, guild_id) -> None:
    cost = 100
    balance = get_coins(message.author.id, guild_id)

    if balance < cost:
        await message.reply(f"you need {cost} joosecoins to buy this! you have {balance}.")
        return

    if len(message.mentions) != 1:
        await message.reply("must mention a user to wtaer!")
        return

    target = message.mentions[0]

    try:
        await target.send(f"# WTAER BRO {get_emoji('bro')}")
        edit_coins(message.author.id, -cost, guild_id)
        await message.reply(f"wtaer'd <@{target.id}>! {cost} joosecoins deducted.")
    except Exception as e:
        await message.reply(str(e))


async def buy_message(message: discord.Message, guild_id) -> None:
    cost = 300
    balance = get_coins(message.author.id, guild_id)

    if balance < cost:
        await message.reply(f"you need {cost} joosecoins to buy this! you have {balance}.")
        return

    if len(message.mentions) != 1:
        await message.reply("must mention a user to message!")
        return

    if len(message.content.split()) < 4:
        await message.reply("must provide a message to send!")
        return

    target = message.mentions[0]
    message_text = message.content.split(maxsplit=3)[3]

    try:
        await target.send(message_text)
        edit_coins(message.author.id, -cost, guild_id)
        await message.reply(f"sent {message_text} to <@{target.id}>! {cost} joosecoins deducted.")
    except Exception as e:
        await message.reply(str(e))

def assassination_chance(coins):
    coins = max(1, min(coins, 3000))
    MIN_CHANCE = 0.05
    MAX_CHANCE = 0.33
    return MIN_CHANCE + (coins / 3000) * (MAX_CHANCE - MIN_CHANCE)


async def buy_assassination(message, guild_id):
    parts = message.content.split()

    if len(message.mentions) != 1:
        await message.reply("must mention a user to assassinate!")
        return

    if len(parts) < 4:
        await message.reply("must provide an amount to invest!")
        return

    try:
        coins = int(parts[3])
    except ValueError:
        await message.reply("amount must be an integer!")
        return

    if coins < 1:
        await message.reply("you must invest at least 1 joosecoin!")
        return
    if coins > 3000:
        await message.reply("you can invest at most 3000 joosecoins into a hit!")
        return

    target = message.mentions[0]
    if target.id == message.author.id:
        await message.reply("you can't assassinate yourself!")
        return

    balance = get_coins(message.author.id, guild_id)
    if balance < coins:
        await message.reply(f"you need {coins} joosecoins to attempt this! you have {balance}.")
        return

    target_balance = get_coins(target.id, guild_id)
    if(balance > target_balance):
        await message.reply(f"please dont kill poor people :c")
        return

    edit_coins(message.author.id, -coins, guild_id)
    edit_stat(message.author.id, guild_id, "assassination", "attempts")

    chance = assassination_chance(coins)
    if random.random() < chance:
        stolen = int(round(target_balance * random.uniform(0.01, 0.03)))
        set_coins(target.id, 0, guild_id)
        coins = load_coins()
        if str(target.id) in coins.get(str(guild_id), {}):
            del coins[str(guild_id)][str(target.id)]
            save_coins(coins)

        edit_coins(message.author.id, stolen, guild_id)
        edit_stat(message.author.id, guild_id, "assassination", "successes")
        edit_stat(message.author.id, guild_id, "assassination", "stolen", stolen)
        edit_stat(target.id, guild_id, "assassination", "times_assassinated")
        await message.reply(
            random_assassination_message(message.author.id, target.id, stolen)
        )
    else:
        edit_stat(message.author.id, guild_id, "assassination", "failures")
        edit_stat(message.author.id, guild_id, "assassination", "lost_to_assassination", coins)
        await message.reply(
            f"<@{message.author.id}>'s assassination attempt on <@{target.id}> failed! "
        )

def random_assassination_message(attacker_id, target_id, stolen):
    return random.choice([
        f"<@{attacker_id}> stabbed <@{target_id}> {random.randint(5,25)} times and stole {stolen} joosecoins!",
        f"<@{attacker_id}> leaned a hitman against <@{target_id}> and stole {stolen} joosecoins!",
        f"<@{attacker_id}> hitman'd <@{target_id}> and stole {stolen} joosecoins!",
        f"<@{attacker_id}> poisoned <@{target_id}> and stole {stolen} joosecoins!",
        f"<@{attacker_id}> set up a trap for <@{target_id}> and stole {stolen} joosecoins!",
        f"<@{target_id}> forgot to pay the cheese tax to  <@{attacker_id}>, and was thus murdered, stealing {stolen} joosecoins!",
        f"<@{attacker_id}> sent <@{target_id}> to the gulag, and stole {stolen} joosecoins!"
    ])
