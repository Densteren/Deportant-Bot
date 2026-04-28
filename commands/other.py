import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timezone as dt_timezone, timedelta
from storage.storage import save_blocked_dm_us, load_blocked_dm_us, bd_users, save_bd_users, load_bd_users
from tools.utils import parse_timezone, format_age, format_message_content, format_month, format_day
from main import BOT
from tools.config import LOG_COMMAND_CHANNEL, OWNER_ROLE, ADMIN_TICKET, OWNERS


class BlockDmCmd(app_commands.Group):
 def __init__(self):
        super().__init__(name="block_dm", description="команды для списка блока лс")
 @app_commands.command(name="add", description="заблокировать получение сообщений от пользователя в лс бота") #@commands.is_owner()   или @commands.has_permissions(administrator=True)
 @app_commands.describe(user="кого заблокировать")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def blockdm(self, interaction: discord.Interaction, user: discord.User):
    blocked_dm_users = load_blocked_dm_us()
    if user.id not in blocked_dm_users:
        blocked_dm_users.add(user.id)
        save_blocked_dm_us(blocked_dm_users)
        result_msg = "Пользователь {user.mention} заблокирован в ЛС."
    else: result_msg = "Этот пользователь уже заблокирован."
    await interaction.response.send_message(content=result_msg, ephemeral=True)
    
    log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    if log_channel:
        log_text = discord.Embed(
        title = "Блокировка ЛС",
        description = f"{interaction.user.mention} использовал `/block_dm add {user.mention}` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.red(),
        timestamp=now
        )
        await log_channel.send(content=f"<@640069373108813824>",embed=log_text)

 @app_commands.command(name="list", description="лист заблокированных пользователей в лс бота")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def blockdmlist(self, interaction: discord.Interaction):
    guild = interaction.guild
    owner_role = guild.get_role(OWNER_ROLE)
    admin_ticket = guild.get_role(ADMIN_TICKET)

    if owner_role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
       result_msg = await interaction.response.send_message("Вы не имеете прав на добавление в блок.", ephemeral=True)
       return

    lines = []
    blocked_dm_users = load_blocked_dm_us()
    if not blocked_dm_users:
        result_msg = await interaction.response.send_message("Список заблокированных пуст.", ephemeral=True)
        return
    for user_id in blocked_dm_users:
        user = guild.get_member(user_id)
        if user:
            lines.append(f"• {user.mention} (`{user.id}`)")
        else:
            lines.append(f"• <@&{user_id}> (удален или недоступен)")

    text = " ".join(lines)
    embed = discord.Embed(
        description=f"### Список заблокированных:\n{text}"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    msg = await interaction.original_response()
    result_msg = format_message_content(msg)

    log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    if log_channel:
        log_text = discord.Embed(
        title = "Блокировка ЛС",
        description = f"{interaction.user.mention} использовал `/block_dm list` в {interaction.channel.mention}\n```{result_msg}```",
        color=discord.Color.yellow(),
        timestamp=now
        )
        await log_channel.send(embed=log_text)

 @app_commands.command(name="remove", description="разблокировать получение сообщений от пользователя в лс бота") #@commands.is_owner()
 @app_commands.describe(user="кого разблокировать")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def unblockdm(self, interaction: discord.Interaction, user: discord.User):
    blocked_dm_users = load_blocked_dm_us()
    if user.id in blocked_dm_users:
        blocked_dm_users.remove(user.id)
        save_blocked_dm_us(blocked_dm_users)
        result_msg = f"{user.mention} разблокирован."
    else:
        result_msg = "Этот пользователь не был заблокирован."
    await interaction.response.send_message(content=result_msg, ephemeral=True)
    
    log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    if log_channel:
        log_text = discord.Embed(
        title = "Разблокировка ЛС",
        description = f"{interaction.user.mention} использовал `/block_dm remove {user.mention}` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.red(),
        timestamp=now
        )
        await log_channel.send(content=f"<@640069373108813824>",embed=log_text)

GMT = [
    app_commands.Choice(name="GMT +0", value="+0"),
    app_commands.Choice(name="GMT +1", value="+1"),
    app_commands.Choice(name="GMT +2", value="+2"),
    app_commands.Choice(name="GMT +3", value="+3"),
    app_commands.Choice(name="GMT +4", value="+4"),
    app_commands.Choice(name="GMT +5", value="+5"),
    app_commands.Choice(name="GMT +6", value="+6"),
    app_commands.Choice(name="GMT +7", value="+7"),
    app_commands.Choice(name="GMT +8", value="+8"),
    app_commands.Choice(name="GMT +9", value="+9"),
    app_commands.Choice(name="GMT +10", value="+10"),
    app_commands.Choice(name="GMT +11", value="+11"),
    app_commands.Choice(name="GMT +12", value="+12"),
    app_commands.Choice(name="GMT -1", value="-1"),
    app_commands.Choice(name="GMT -2", value="-2"),
    app_commands.Choice(name="GMT -3", value="-3"),
    app_commands.Choice(name="GMT -4", value="-4"),
    app_commands.Choice(name="GMT -5", value="-5"),
    app_commands.Choice(name="GMT -6", value="-6"),
    app_commands.Choice(name="GMT -7", value="-7"),
    app_commands.Choice(name="GMT -8", value="-8"),
    app_commands.Choice(name="GMT -9", value="-9"),
    app_commands.Choice(name="GMT -10", value="-10"),
    app_commands.Choice(name="GMT -11", value="-11"),
    app_commands.Choice(name="GMT -12", value="-12")
]
class BirthdayCmd(app_commands.Group):
 def __init__(self):
        super().__init__(name="birthday", description="команды для списка дней рождения")
 @app_commands.command(name="add", description="добавить день рождение")
 @app_commands.describe(
    user="чей день рождения",
    day="день",
    month="месяц",
    year="год",
    timezone="часовой пояс GMT (например +3 или +7)"
)
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 @app_commands.choices(timezone=GMT)
 async def addbd(self, interaction: discord.Interaction, user: discord.User, day: int, month: int, timezone: str, year: int | None, note: str | None):
    guild = interaction.guild
    owner_role = guild.get_role(OWNER_ROLE)
    admin_ticket = guild.get_role(ADMIN_TICKET)
    if owner_role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
       result_msg = "⚠️ Вы не имеете прав на добавление."
       await interaction.response.send_message(content=result_msg, ephemeral=True)
       return
    
    #tzinfo = parse_timezone(timezone)
    #if not tzinfo:
    #    result_msg = "❌ Укажи часовой пояс в формате +3 или -5"
    #    return await interaction.response.send_message(content=result_msg, ephemeral=True)
    bd_users = load_bd_users()
    if user.id in bd_users:
        result_msg =  "⚠️ День рождения уже добавлен."
        await interaction.response.send_message(content=result_msg, ephemeral=True)
        return

    bd_users[user.id] = {
        "nickname": user.display_name,
        "day": day,
        "month": month,
        "year": year,
        "timezone": timezone,
        "note": note
    }
    save_bd_users(bd_users)
    msk = dt_timezone(timedelta(hours=3))
    now = datetime.now(msk)
    result_msg = f"🎂 День рождения {user.mention} добавлен (UTC{timezone})"
    await interaction.response.send_message(content=result_msg, ephemeral=True)
    
    log_channel = guild.get_channel(LOG_COMMAND_CHANNEL)
    if log_channel:
        log_text = discord.Embed(
        title = "Добавление дня рождения",
        description = f"{interaction.user.mention} использовал `/birthday add {user.mention} {day} {month} {year} {timezone}` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.green(),
        timestamp=now
        )
        await log_channel.send(embed=log_text)
 
 @app_commands.command(name="list", description="список всех дней рождений")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def bdlist(self, interaction: discord.Interaction):
    guild = interaction.guild
    if not bd_users:
        result_msg = await interaction.response.send_message("⚠️ Список пуст.", ephemeral=True)
        return

    lines = []
    now_utc = datetime.now(dt_timezone.utc)
    bd_users_time = load_bd_users()
    for user_id, data in bd_users_time.items():
        tz = parse_timezone(data["timezone"])
        local_time = now_utc.astimezone(tz)
        user = guild.get_member(user_id)
        note = ""
        if data["note"] is not None:
            note = f'\n* Примечание(я): {data["note"]}'
        if not user:
            try:
                user = await guild.fetch_member(user_id)
            except (discord.NotFound, discord.Forbidden):
                user = None
        if data["year"]:
            birthday_passed = ((local_time.month, local_time.day) >= (data["month"], data["day"]))
            age = local_time.year - data["year"] - (0 if birthday_passed else 1)
            age_ys = format_age(age)
            month = format_month(data["month"])
            day = format_day(data["day"])
            if user:
                lines.append(f'### {user.mention} (`{user.id}`) — {age_ys};\n* День рождения: {day}.{month}.{data["year"]};\n* Метсное время: {tz}{note}')
            else:
                lines.append(f'### <@{user_id}> (удален или недоступен) — {age_ys};\n* День рождения: {day}.{month}.{data["year"]};\n* Метсное время: {tz}{note}')
        else:
            if user:
                lines.append(f'### {user.mention} (`{user.id}`):\n* День рождения: {day}.{month};\n* Метсное время:{tz}{note}')
            else:
                lines.append(f'### <@{user_id}> (удален или недоступен):\n* День рождения: {day}.{month}\n* Метсное время:{tz}{note}')

    text = "\n".join(lines)
    embed = discord.Embed(
        description=f"### Список дней рождений:\n{text}"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    msg = await interaction.original_response()
    result_msg = format_message_content(msg)

    log_channel = guild.get_channel(LOG_COMMAND_CHANNEL)
    msk = dt_timezone(timedelta(hours=3))
    now = datetime.now(msk)
    if log_channel:
        log_text = discord.Embed(
        title = "Простотрм дней рождений",
        description = f"{interaction.user.mention} использовал `/birthday list` в {interaction.channel.mention}\n```{result_msg}```",
        color=discord.Color.yellow(),
        timestamp=now
        )
        await log_channel.send(embed=log_text)

 @app_commands.command(name="remove", description="разблокировать получение сообщений от пользователя в лс бота") #@commands.is_owner()
 @app_commands.describe(user="удалить день рождение")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def removebd(self, interaction: discord.Interaction, user: discord.User):
    guild = interaction.guild
    owner_role = guild.get_role(OWNER_ROLE)
    admin_ticket = guild.get_role(ADMIN_TICKET)
    if owner_role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
       result_msg = "⚠️ Вы не имеете прав на удаление."
       return await interaction.response.send_message(content=result_msg, ephemeral=True)
    
    bd_users = load_bd_users()
    if str(user.id) in bd_users:
        bd_users.pop(str(user.id))
        save_bd_users(bd_users)
        result_msg = f"🗑️ День рождение {user.mention} удалён."
    else:
        result_msg = "⚠️ День рождения ещё не добавлен."
    await interaction.response.send_message(content=result_msg, ephemeral=True)
    
    log_channel = guild.get_channel(LOG_COMMAND_CHANNEL)
    msk = dt_timezone(timedelta(hours=3))
    now = datetime.now(msk)
    if log_channel:
        log_text = discord.Embed(
        title = "Удаление дня рождения",
        description = f"{interaction.user.mention} использовал `/birthday remove {user.mention}` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.red(),
        timestamp=now
        )
        await log_channel.send(content=f"<@640069373108813824>",embed=log_text)

class CloseDMView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Send from Deportant", style=discord.ButtonStyle.url, url="https://discord.com/channels/1341738075113390132"))
        self.add_item(HideMsgDM())        
    
class HideMsgDM(discord.ui.Button):
    def __init__(self): super().__init__(style=discord.ButtonStyle.gray, custom_id="dm:hide", emoji="<:silent_voice_cross:1493090054736969759>")
    async def callback(self, interaction: discord.Interaction): await interaction.message.delete()
