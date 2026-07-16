import asyncio
import discord
import json
import os
import random
import math
from emoji import EMOJI_DATA

COINS_FILE = os.path.join(os.path.dirname(__file__), "coins.json")


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

async def give_coins(sender, reciever, amt):
    if get_coins(sender) > amt:
        edit_coins(sender, -amt)
        edit_coins(reciever, amt)
        return(amt)
    else:
        true_coins = get_coins(reciever)
        edit_coins(sender, true_coins)
        set_coins(reciever, 0)
        return(true_coins)


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

class AppEmoji:
    # claude cant code™

    def __init__(self, data: dict, application_id: int):
        self.id = int(data["id"])
        self.name = data["name"]
        self.animated = data.get("animated", False)
        self._application_id = application_id
        self._url = f"https://cdn.discordapp.com/emoji/{self.id}.{'gif' if self.animated else 'png'}"

    @property
    def url(self) -> str:
        return self._url

    def __str__(self) -> str:
        return f"<:{self.name}:{self.id}>"

    def __repr__(self) -> str:
        return f"AppEmoji(name={self.name!r}, id={self.id})"


EMOJI = []


async def load_emoji(client: discord.Client):
    global EMOJI
    EMOJI = list(client.emojis)

    try:
        data = await client.http.get_application_emojis(client.application_id)
        for e in data.get("items", data if isinstance(data, list) else []):
            EMOJI.append(AppEmoji(e, client.application_id))
    except Exception as exc:
        print(f"Failed to load application emojis: {exc}")


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
    mode = random.randint(0, 2)
    if mode == 0:
        await slot_machine(message, coins)
        edit_coins(message.author.id, -coins)
    elif mode == 1:
        # await slot_machine(message, coins)
        await roulette_wheel(message, coins)
        edit_coins(message.author.id, -coins)
    elif mode == 2:
        await chance_time(message, coins)


async def slot_machine(message: discord.Message, coins: int) -> None:
    emoji_pool = all_emojis()
    frames = []
    for i in range(5):
        pick = random.sample(emoji_pool, 3)
        if random.randint(0, 2) == 0:
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
    score_msg, winnings = slot_score(final, coins)
    edit_coins(message.author.id, winnings)
    await msg.edit(content=build_slot_display(final, spinning=False) + "\n" + score_msg)


def build_slot_display(emojis: list, spinning: bool = False) -> str:
    e = [str(e) for e in emojis]
    return f"slot machine\n│  {e[0]}  │  {e[1]}  │   {e[2]}  │"


def slot_score(emojis: list, coins: int) -> tuple[str, int]:
    e = [str(e) for e in emojis]
    counts = {}
    for icon in e:
        counts[icon] = counts.get(icon, 0) + 1
    best = max(counts.values())
    if best == 3:
        winnings = int(round(coins * random.uniform(2, 4)))
    elif best == 2:
        winnings = int(round(coins * random.uniform(1.3, 1.7)))
    else:
        winnings = int(round(coins * random.uniform(0.3, 0.9)))
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
    score_msg, winnings = roulette_score(landed, coins)
    edit_coins(message.author.id, winnings)
    await msg.edit(
        content=build_roulette_display(final, spinning=False) + "\n" + score_msg
    )


def build_roulette_display(squares: list, spinning: bool = False) -> str:
    return f"roulette wheel\n⬛ ⬛ ⬇️ ⬛ ⬛\n{squares[0]} {squares[1]} {squares[2]} {squares[3]} {squares[4]}\n⬛ ⬛ ⬆️ ⬛ ⬛"


def roulette_score(landed: str, coins: int) -> tuple[str, int]:
    if landed == "🟩":
        winnings = int(round(coins * random.uniform(2.0, 4.0)))
        return f"you landed on 🟩\nyou received: {winnings} joosecoins", winnings
    elif landed == "🟥":
        winnings = int(round(coins * random.uniform(1.3, 1.7)))
        return f"you landed on 🟥\nyou received: {winnings} joosecoins", winnings
    else:
        winnings = int(round(coins * random.uniform(0.4, 0.9)))
        return f"you landed on ⬛\nyou received: {winnings} joosecoins", winnings


def get_random_other_player(user) -> str:
    pl = random.choice(get_all_coins())[0]
    while pl == user:
        pl = random.choice(get_all_coins())[0]
    return pl


async def chance_time(message, coins):
    author = message.author.id
    # direction = random.choice(["⬅️", "➡️", "communism"])
    direction = "communism"
    random_player = int(get_random_other_player(author))
    txt = f"<@{author}>"
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
        txt += f"\n<@{author}> stole {stolen} joosecoins from <@{random_player}>"
        await msg.edit(content=txt)

    elif (direction) == "➡️":
        stolen = await give_coins(author, random_player, coins)
        txt += f"\n<@{random_player}> stole {stolen} joosecoins from <@{author}>"
        await msg.edit(content=txt)
    elif (direction) == "communism":
        total = get_coins(author) + get_coins(random_player)
        set_coins(author, int(math.floor(total/2)))
        set_coins(random_player, int(math.floor(total/2)))
        txt += f"\n<@{author}> and <@{random_player}> shared {total} joosecoins"
        await msg.edit(content=txt)

async def bankruptcy(message):
    if get_coins(message.author.id) <= 4:
        set_coins(message.author.id, 5)
        await message.reply(
            "you filed for bankruptcy and now have 5 joosecoins because I felt bad for you"
        )
    else:
        await message.reply("you are too rich to file for bankruptcy")
