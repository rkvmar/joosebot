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


def load_coins() -> dict:
    if not os.path.exists(COINS_FILE):
        return {}
    with open(COINS_FILE, "r") as f:
        return json.load(f)


def save_coins(coins: dict) -> None:
    with open(COINS_FILE, "w") as f:
        json.dump(coins, f, indent=2)


def get_coins(user_id: int) -> int:
    coins = load_coins()
    key = str(user_id)
    if key not in coins:
        coins[key] = 100
        save_coins(coins)
        return 100
    return coins[key]


def edit_coins(user_id: int, amount: int) -> int:
    coins = load_coins()
    key = str(user_id)
    coins[key] = int(coins.get(key, 0) + amount)
    save_coins(coins)
    return coins[key]


def set_coins(user_id: int, amount: int) -> int:
    coins = load_coins()
    key = str(user_id)
    coins[key] = int(amount)
    save_coins(coins)
    return coins[key]


def reset_all_coins() -> None:
    save_coins({})


def get_all_coins() -> list[tuple[int, int]]:
    coins = load_coins()
    return sorted(
        [(int(uid), amount) for uid, amount in coins.items()], key=lambda x: -x[1]
)


def load_stats() -> dict:
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, "r") as f:
        return json.load(f)


def save_stats(stats: dict) -> None:
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def default_stats():
    return {
        "gambles": 0,
        "slot": {"plays": 0, "wagered": 0, "won": 0, "nothings": 0, "pairs": 0, "jackpots": 0},
        "roulette": {"plays": 0, "wagered": 0, "won": 0, "blacks": 0, "reds": 0, "jackpots": 0},
        "chance": {"plays": 0, "stolen_from_others": 0, "stolen_by_others": 0, "communism": 0},
        "bankruptcy": 0,
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

def get_user_stats(user_id: int):
    stats = load_stats()
    key = str(user_id)
    if key not in stats:
        stats[key] = default_stats()
    else:
        stats[key] = fill_missing(stats[key])
    save_stats(stats)
    return stats[key]



def edit_stat(user_id: int, category: str, stat: str = None, amount: int = 1) -> None:
    stats = load_stats()
    key = str(user_id)
    if key not in stats:
        stats[key] = default_stats()

    if stat is None:
        stats[key][category] += amount
    else:
        stats[key][category][stat] += amount

    save_stats(stats)


async def parse_stats(message: discord.Message) -> None:
    target = message.mentions[0] if message.mentions else message.author
    s = get_user_stats(target.id)

    net_slot = s["slot"]["won"] - s["slot"]["wagered"]
    net_roulette = s["roulette"]["won"] - s["roulette"]["wagered"]

    txt = f"## stats for <@{target.id}>\n"
    txt += f"total gambles: {s['gambles']}\n\n"
    txt += f"**slots** — plays: {s['slot']['plays']}, wagered: {s['slot']['wagered']}, won: {s['slot']['won']}, nothings: {s['slot']['nothings']}, pairs: {s['slot']['pairs']}, jackpots: {s['slot']['jackpots']} (net {net_slot})\n"
    txt += f"**roulette** — plays: {s['roulette']['plays']}, wagered: {s['roulette']['wagered']}, won: {s['roulette']['won']}, blacks: {s['roulette']['blacks']}, reds: {s['roulette']['reds']}, jackpots: {s['roulette']['jackpots']} (net {net_roulette})\n"
    txt += f"**chance time** — plays: {s['chance']['plays']}, stolen from others: {s['chance']['stolen_from_others']}, stolen by others: {s['chance']['stolen_by_others']}, communism: {s['chance']['communism']}\n"
    txt += f"times gone bankrupt: {s['bankruptcy']}\n\n"

    await message.reply(txt)


async def give_coins(sender, reciever, amt):
    if get_coins(sender) > amt:
        edit_coins(sender, -amt)
        edit_coins(reciever, amt)
        return(amt)
    else:
        true_coins = get_coins(sender)
        edit_coins(reciever, true_coins)
        set_coins(sender, 0)
        return(true_coins)

async def parse_give(message: discord.Message) -> None:
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

    given = await give_coins(sender, receiver, coins)

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
    parts = message.content.split()

    if len(parts) < 2:
        await message.reply("must provide coins!")
        return
    balance = get_coins(message.author.id)
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

    edit_stat(message.author.id, "gambles")

    mode = random.randint(0, 2)
    if mode == 0:
        edit_coins(message.author.id, -coins)
        edit_stat(message.author.id, "slot", "plays")
        edit_stat(message.author.id, "slot", "wagered", coins)
        await slot_machine(message, coins)
    elif mode == 1:
        # await slot_machine(message, coins)
        edit_coins(message.author.id, -coins)
        edit_stat(message.author.id, "roulette", "plays")
        edit_stat(message.author.id, "roulette", "wagered", coins)
        await roulette_wheel(message, coins)
    elif mode == 2:
        edit_stat(message.author.id, "chance", "plays")
        await chance_time(message, coins)


async def slot_machine(message: discord.Message, coins: int) -> None:
    emoji_pool = all_emojis()
    frames = []
    for i in range(5):
        pick = random.sample(emoji_pool, 3)
        if random.randint(0, 1) == 0:
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
    score_msg, winnings = slot_score(final, coins, message.author.id)
    edit_coins(message.author.id, winnings)
    edit_stat(message.author.id, "slot", "won", winnings)
    await msg.edit(content=build_slot_display(final, spinning=False) + "\n" + score_msg)


def build_slot_display(emojis: list, spinning: bool = False) -> str:
    e = [str(e) for e in emojis]
    return f"**slot machine**\n│  {e[0]}  │  {e[1]}  │   {e[2]}  │"


def slot_score(emojis: list, coins: int, author) -> tuple[str, int]:
    e = [str(e) for e in emojis]
    counts = {}
    for icon in e:
        counts[icon] = counts.get(icon, 0) + 1
    best = max(counts.values())
    if best == 3:
        edit_stat(author, "slot", "jackpots")
        winnings = int(round(coins * random.uniform(2, 4)))
    elif best == 2:
        edit_stat(author, "slot", "pairs")
        winnings = int(round(coins * random.uniform(1.3, 1.7)))
    else:
        edit_stat(author, "slot", "nothings")
        winnings = int(round(coins * random.uniform(0.5, 0.9)))
    return f"you recieved: {winnings} joosecoins", winnings


async def parse_roulette(message: discord.Message) -> None:
    parts = message.content.split()

    if len(parts) < 2:
        await message.reply("must provide coins!")
        return

    try:
        coins = int(parts[1])
    except ValueError:
        await message.reply("coins must be an integer!")
        return

    balance = get_coins(message.author.id)
    if balance < coins:
        await message.reply(f"you only have {balance} joosecoins!")
        return

    if coins < 1:
        await message.reply("you must gamble at least 1 joosecoin!")
        return

    edit_coins(message.author.id, -coins)
    edit_stat(message.author.id, "roulette", "plays")
    edit_stat(message.author.id, "roulette", "wagered", coins)
    await roulette_wheel(message, coins)


async def roulette_wheel(message, coins):
    RED = "🟥"
    BLACK = "⬛"
    GREEN = "🟩"

    strip_length = 25
    first_color = random.choice([RED, BLACK])
    strip = []
    for i in range(strip_length):
        if random.random() < 0.10 and (not strip or strip[-1] != GREEN):
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
    score_msg, winnings = roulette_score(landed, coins, message.author.id)
    edit_coins(message.author.id, winnings)
    edit_stat(message.author.id, "roulette", "won", winnings)
    await msg.edit(
        content=build_roulette_display(final, spinning=False) + "\n" + score_msg
    )


def build_roulette_display(squares: list, spinning: bool = False) -> str:
    return f"**roulette wheel**\n⬛ ⬛ ⬇️ ⬛ ⬛\n{squares[0]} {squares[1]} {squares[2]} {squares[3]} {squares[4]}\n⬛ ⬛ ⬆️ ⬛ ⬛"


def roulette_score(landed: str, coins: int, author) -> tuple[str, int]:
    if landed == "🟩":
        edit_stat(author, "roulette", "jackpots")
        winnings = int(round(coins * random.uniform(2.0, 4.0)))
        return f"you landed on 🟩\nyou received: {winnings} joosecoins", winnings
    elif landed == "🟥":
        edit_stat(author, "roulette", "reds")
        winnings = int(round(coins * random.uniform(1.3, 1.7)))
        return f"you landed on 🟥\nyou received: {winnings} joosecoins", winnings
    else:
        edit_stat(author, "roulette", "blacks")
        winnings = int(round(coins * random.uniform(0.4, 0.9)))
        return f"you landed on ⬛\nyou received: {winnings} joosecoins", winnings


def get_random_other_player(user) -> str:
    pl = random.choice(get_all_coins())[0]
    while pl == user:
        pl = random.choice(get_all_coins())[0]
    return pl


async def chance_time(message, coins):
    author = message.author.id
    direction = random.choice(["⬅️", "➡️","⬅️", "➡️","⬅️", "➡️","⬅️", "➡️","⬅️", "➡️","⬅️", "➡️","⬅️", "➡️", "communism"])
    # direction = "communism"
    random_player = int(get_random_other_player(author))
    if(direction == "⬅️"):
        while(get_coins(random_player) <= 0):
            random_player = int(get_random_other_player(author))
    txt = f"**chance time!**\n<@{author}>"
    msg = await message.reply(txt)
    await asyncio.sleep(1)
    if direction == "communism":
        txt += f" {random.choice(all_emojis())}"
    else:
        txt += f" {direction}"
    await msg.edit(content=txt)
    await asyncio.sleep(1)
    txt += f" <@{random_player}>"
    await msg.edit(content=txt)
    await asyncio.sleep(1)

    if (direction) == "⬅️":
        stolen = await give_coins(random_player, author, coins)
        edit_stat(author, "chance", "stolen_from_others", stolen)
        edit_stat(random_player, "chance", "stolen_by_others", stolen)
        txt += f"\n<@{author}> stole {stolen} joosecoins from <@{random_player}>"
        await msg.edit(content=txt)

    elif (direction) == "➡️":
        stolen = await give_coins(author, random_player, coins)
        edit_stat(random_player, "chance", "stolen_from_others", stolen)
        edit_stat(author, "chance", "stolen_by_others", stolen)
        txt += f"\n<@{random_player}> stole {stolen} joosecoins from <@{author}>"
        await msg.edit(content=txt)
    elif (direction) == "communism":
        total = get_coins(author) + get_coins(random_player)
        set_coins(author, int(math.floor(total/2)))
        set_coins(random_player, int(math.floor(total/2)))
        edit_stat(author, "chance", "communism")
        edit_stat(random_player, "chance", "communism")
        txt += f"\n<@{author}> and <@{random_player}> shared {total} joosecoins"
        await msg.edit(content=txt)

async def bankruptcy(message):
    if get_coins(message.author.id) <= 10:
        set_coins(message.author.id, 10)
        edit_stat(message.author.id, "bankruptcy")
        await message.reply(
            "you filed for bankruptcy and now have 10 joosecoins because I felt bad for you"
        )
    else:
        await message.reply("you are too rich to file for bankruptcy")


async def parse_buy(message: discord.Message, client: discord.Client) -> None:
    parts = message.content.split()

    if len(parts) < 2:
        await message.reply("must provide an item to buy!")
        return

    item = parts[1].lower()

    if item == "pfp":
        await buy_pfp(message, client)
    elif item == "wtaer":
        await buy_wtaer(message)
    elif item == "message":
        await buy_message(message)
    else:
        await message.reply(f"unknown item: {item}")


async def buy_pfp(message: discord.Message, client: discord.Client) -> None:
    cost = 500
    balance = get_coins(message.author.id)

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
        edit_coins(message.author.id, -cost)
        await message.reply(f"profile picture changed! {cost} joosecoins deducted.")
    except discord.HTTPException as e:
        await message.reply(str(e))
    except Exception as e:
        await message.reply(str(e))


async def buy_wtaer(message: discord.Message) -> None:
    cost = 100
    balance = get_coins(message.author.id)

    if balance < cost:
        await message.reply(f"you need {cost} joosecoins to buy this! you have {balance}.")
        return

    if len(message.mentions) != 1:
        await message.reply("must mention a user to wtaer!")
        return

    target = message.mentions[0]

    try:
        await target.send(f"# WTAER BRO {get_emoji('bro')}")
        edit_coins(message.author.id, -cost)
        await message.reply(f"wtaer'd <@{target.id}>! {cost} joosecoins deducted.")
    except Exception as e:
        await message.reply(str(e))

async def buy_message(message: discord.Message) -> None:
    cost = 300
    balance = get_coins(message.author.id)

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
        edit_coins(message.author.id, -cost)
        await message.reply(f"sent {message_text} to <@{target.id}>! {cost} joosecoins deducted.")
    except Exception as e:
        await message.reply(str(e))
