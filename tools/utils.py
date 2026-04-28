import discord, random
from datetime import datetime, timezone as dt_timezone, timedelta, timezone
from main import BOT
from tools.config import GUILD_ID, PROTECTED_ROLES, PROTECTED_USERS, EXCLUDED_CATEGORIES, EXCLUDED_CHANNELS, GENERAL_ROLE

message_counter = {}

def parse_time(time_str):
    units = {"m": 60, "h": 3600, "d": 86400, "w": 604800}
    try:
        return int(time_str[:-1]) * units[time_str[-1]]
    except:
        return None

def parse_timezone(offset: str) -> dt_timezone | None:
    try:
        sign = 1 if offset.startswith("+") else -1
        value = offset[1:]

        if ":" in value:
            hours, minutes = map(int, value.split(":"))
        else:
            hours = int(value)
            minutes = 0

        if hours > 14 or minutes >= 60:
            return None

        return dt_timezone(sign * timedelta(hours=hours, minutes=minutes))
    except Exception:
        return None

def is_time_formate(arg:str):
    return arg[-1] in ("m", "h", "d", "w") and arg[:-1].isdigit()

def format_age(age: int) -> str:
    if 11 <= age % 100 <= 14:
        return f"{age} лет"

    last = age % 10
    if last == 1:
        return f"{age} год"
    elif 2 <= last <= 4:
        return f"{age} года"
    else:
        return f"{age} лет"

def format_month(month: int) -> str:
    if 1 <= month <= 9:
        return f"0{month}"
    else:
        return f"{month}"

def format_day(day: int) -> str:
    if 1 <= day <= 9:
        return f"0{day}"
    else:
        return f"{day}"

async def get_members(role_ids):
    guild = BOT.get_guild(GUILD_ID)
    if isinstance(role_ids, int): role_ids = [role_ids]
    if not role_ids: return ""
    members = []
    for rid in role_ids:
        role = guild.get_role(rid)  # <- и тут
        if not role:
            try: role = await guild.fetch_role(rid)
            except discord.NotFound:
                print(f"Роль с ID {rid} не найдена!")
                continue
        for m in role.members:
            if guild.get_role(GENERAL_ROLE) not in m.roles: continue
            members.append(m.mention)
    return " ".join(members) if members else ""

def is_protected(interaction, member: discord.Member) -> bool:
    if member.id in PROTECTED_USERS:
        return True
    if any(role.id in PROTECTED_ROLES for role in member.roles):
        return True
    if member.guild_permissions.administrator:
        return True
    if member.top_role >= interaction.guild.me.top_role:
        return True
    if member == interaction.user:
        return True
    if member == interaction.guild.me:
        return True
    return False

def generate_random_id():
    now = datetime.now(timezone(timedelta(hours=3)))
    hour = now.hour
    if 2 <= hour < 6:
        shift = "01"
    elif 6 <= hour < 10:
        shift = "02"
    elif 10 <= hour < 14:
        shift = "03"
    elif 14 <= hour < 18:
        shift = "04"
    elif 18 <= hour < 22:
        shift = "05"
    else:
        shift = "06"
    date_str = now.strftime("%y%m")
    day_str = now.strftime("%d")
    rand = random.randint(1000, 9999)
    return f"{date_str}-{day_str}{shift}-{rand}"

def format_message_content(message: discord.Message) -> str:
    parts = []

    # Текст
    if message.content:
        parts.append(message.content)

    # Файлы / изображения
    for attachment in message.attachments:
        parts.append(f"[Файл]({attachment.url})")

    # Стикеры
    for sticker in message.stickers:
        parts.append(f"[Стикер]({sticker.url})")

    # Эмбеды (если отправлены не ботом)
    for embed in message.embeds:
        if embed.title:
            parts.append(f"**{embed.title}**")

        if embed.description:
            parts.append(embed.description)

        if embed.image and embed.image.url:
            parts.append(f"> [Изображение]({embed.image.url})")

        if embed.thumbnail and embed.thumbnail.url:
            parts.append(f"> [Миниатюра]({embed.thumbnail.url})")

    if not parts:
        return "[контент недоступен]"

    return "\n".join(parts)

async def get_channel_popularity(top_n: int = 3):
    guild = BOT.get_guild(GUILD_ID)
    channel_stats: dict[discord.abc.GuildChannel, int] = {}

    async def process_history(channel):
        try:
            msg_count = 0
            async for msg in channel.history(limit=None):
                msg_count += 1
            channel_stats[channel] = msg_count
        except discord.Forbidden:
            return

    # 🔹 ТЕКСТ + ВОЙС (с чатами)
    for channel in guild.channels:
        if channel.category and channel.category.id in EXCLUDED_CATEGORIES: #channel.id in EXCLUDED_CHANNELS or
            continue
        if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel)):
            await process_history(channel)

        # 🔹 ФОРУМЫ
        elif isinstance(channel, discord.ForumChannel):
            if channel.category and channel.category.id in EXCLUDED_CATEGORIES: #channel.id in EXCLUDED_CHANNELS or
                continue
            for thread in channel.threads:
                await process_history(thread)
    
    if not channel_stats:
        return [], []

    # 🔹 сортировка
    sorted_channels = sorted(
        channel_stats.items(),
        key=lambda item: item[1],
        reverse=True
    )

    most_popular = sorted_channels[:top_n]
    least_popular = sorted_channels[-top_n:][::-1]

    return most_popular, least_popular

async def get_most_active_members_by_messages(top_n: int = 3):
    guild = BOT.get_guild(GUILD_ID)
    member_count: dict[discord.Member, int] = {}

    async def process_history(channel):
        try:
            async for msg in channel.history(limit=None):
                if msg.author and not msg.author.bot:
                    if isinstance(msg.guild, discord.Guild) and msg.guild.get_member(msg.author.id):
                        member_count[msg.author] = member_count.get(msg.author, 0) + 1
        except (discord.Forbidden, AttributeError):
            pass

    # 🔹 ТЕКСТ + ВОЙС (с чатами)
    for channel in guild.channels:
        if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel)):
            await process_history(channel)

        # 🔹 ФОРУМЫ
        elif isinstance(channel, discord.ForumChannel):
            for thread in channel.threads:
                await process_history(thread)

    if not member_count:
        return []

    # сортируем по количеству сообщений (по убыванию)
    sorted_members = sorted(
        member_count.items(),
        key=lambda item: item[1],
        reverse=True
    )

    # берём TOP-N
    return sorted_members[:top_n]

async def get_most_active_members_by_reports(top_n: int = 3):
    guild = BOT.get_guild(GUILD_ID)
    member_count: dict[discord.Member, int] = {}
    role = guild.get_role(1342917264256532643)
    for member in role.members:
        if not member.bot:
            member_count[member] = 0

    async def process_history(channel):
        try:
            async for msg in channel.history(limit=None):
                if msg.author and not msg.author.bot and role in msg.author.roles:
                    if isinstance(msg.guild, discord.Guild) and msg.guild.get_member(msg.author.id):
                        member_count[msg.author] = member_count.get(msg.author, 0) + 1
        except (discord.Forbidden, AttributeError):
            pass

    for channel in guild.channels:
        if channel.id == 1442605503892160662:
            await process_history(channel)

    if not member_count:
        return []

    # сортируем по количеству сообщений (по убыванию)
    most_active_rep = sorted(
        member_count.items(),
        key=lambda item: item[1],
        reverse=True
    )[:top_n]
    least_active_rep_unsort = sorted(
        member_count.items(),
        key=lambda item: item[1]
    )

    most_active_members = {member for member, _ in most_active_rep}

    least_active_rep = []
    for member, count in least_active_rep_unsort:
        if member not in most_active_members:
            least_active_rep.append((member, count))
        if len(least_active_rep) >= top_n:
            break

    # берём TOP-N
    return most_active_rep, least_active_rep

async def log(target, *, kind: str = "embed", content: str | None = None, title: str | None = None, description: str | None = None, footer: str | None = None, timestamp: bool | datetime = False, color: discord.Color | None = None, reply: bool = False):
    # --- собираем payload ---
    payload = {}
    if kind == "text":
        payload["content"] = content or ""
    else:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or discord.Color.blurple()
        )
        if footer:
            embed.set_footer(text=footer)
        if timestamp:
            embed.timestamp = (
                timestamp if isinstance(timestamp, datetime)
                else datetime.utcnow()
            )
        payload["embed"] = embed

    # --- определяем, КУДА отправлять ---
    if isinstance(target, discord.Interaction):
        if not target.response.is_done():
            await target.response.send_message(**payload, ephemeral=False)
        else:
            await target.followup.send(**payload)

    elif isinstance(target, discord.Message):
        if reply:
            await target.reply(**payload)
        else:
            await target.channel.send(**payload)

    elif isinstance(target, discord.abc.Messageable):
        await target.send(**payload)

    else:
        raise TypeError("log(): unsupported target type")