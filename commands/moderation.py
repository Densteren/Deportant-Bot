import discord
from discord import app_commands
from datetime import timedelta, datetime, timezone
import tools.utils as utils
from main import BOT
from tools.config import LOG_COMMAND_CHANNEL


class Модерация(app_commands.Group):
 def __init__(self):
        super().__init__(name="panel", description="модераторские команды")
 # ---PURGE---

 @app_commands.command(name="purge", description="удалить сообщения")
 @app_commands.describe(аргумент="целое число или формат времени")
 @app_commands.allowed_contexts(guilds=True)
 async def purge(self, interaction: discord.Interaction, аргумент: str):
    await interaction.response.defer(ephemeral=True)
    if not interaction.user.guild_permissions.manage_messages: return await interaction.followup.send("У вас нет прав на использование этой команды.", ephemeral=True)

    if utils.is_time_formate(аргумент):
        seconds = utils.parse_time(аргумент)
        if seconds is None: return await interaction.followup.send("Неправильный аргумент: введите целое число без букв (например: `10`) или **формат времени** (`5m`, `2h`).", ephemeral=True)
    else:
        try:
            amount = int(аргумент)
            if amount <= 0: raise ValueError
        except ValueError: return await interaction.followup.send("Неправильный аргумент: введите **целое число** без букв (например: `10`) или формат времени (`5m`, `2h`).", ephemeral=True)
        
    now = datetime.now(timezone(timedelta(hours=3)))        
    try:
        if utils.is_time_formate(аргумент):
            deleted = await interaction.channel.purge(check=lambda m: (now - m.created_at).total_seconds() <= seconds)
            result_msg = f"Удалено {len(deleted)} сообщений за последние {аргумент}."
        else:
            deleted = await interaction.channel.purge(limit=amount)
            result_msg = f"Удалено {len(deleted)} сообщений."

        await interaction.followup.send(result_msg)

        # Логирование
        log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
        if log_channel:
            log_text = discord.Embed(
            title = "Очистка",
            description = f"{interaction.user.mention} использовал `/purge {аргумент}` в {interaction.channel.mention}\n{result_msg}",
            color = discord.Color.red()
            )
            log_text.set_footer(text={len(deleted)})
            log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
            await log_channel.send(content=f"<@640069373108813824>",embed=log_text)

    except Exception as e: return await interaction.followup.send(f"Error unknow: {str(e)}", ephemeral=True)

 # ---KICK---

 @app_commands.command(name="kick", description="кикнуть пользователя")
 @app_commands.describe(участник="кого кикнуть", причина = "необязательно")
 @app_commands.allowed_contexts(guilds=True)
 async def kick(self, interaction: discord.Interaction, участник: discord.Member, причина: str = None):
    await interaction.response.defer(ephemeral=True)
    if not interaction.user.guild_permissions.kick_members: return await interaction.followup.send("У вас нет прав на использование этой команды.", ephemeral=True)
    if utils.is_protected(interaction, участник): return await interaction.followup.send("Данный пользователь защищён от модераторских воздействий.", ephemeral=True)
    now = datetime.now(timezone(timedelta(hours=3)))
    await участник.kick(reason=причина)
    await interaction.followup.send(f"{участник.mention} был кикнут. Причина: {причина or 'не указана'}")

    log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
    if log_channel:
        embed = discord.Embed(title="Кик пользователя", color=discord.Color.red())
        embed.add_field(name="Пользователь", value=участник.mention, inline=False)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=False)
        embed.add_field(name="Причина", value=причина or "не указана", inline=False)
        embed.timestamp = now
        embed.color = discord.Color.red()
        embed.set_footer(text={участник.id})
        embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        await log_channel.send(content=f"<@640069373108813824>",embed=embed)

 #---MUTE---

 @app_commands.command(name="mute", description="замьютить пользователя")
 @app_commands.describe(участник="кого замьютить", время="формат времени", причина="необязательно")
 @app_commands.allowed_contexts(guilds=True)
 async def mute(self, interaction: discord.Interaction, участник: discord.Member, время: str, причина: str = None):
    await interaction.response.defer(ephemeral=True)
    if not interaction.user.guild_permissions.moderate_members: return await interaction.followup.send("У вас нет прав на использование этой команды.", ephemeral=True)

    seconds = utils.parse_time(время)
    if seconds is None: return await interaction.followup.send("Неправильный аргумент: введите формат времени (например: `5m`, `2h`).", ephemeral=True)
    if utils.is_protected(interaction, участник): return await interaction.followup.send("Данный пользователь защищён от модераторских воздействий.", ephemeral=True)
    now = datetime.now(timezone(timedelta(hours=3)))
    try:
        await участник.timeout(now + timedelta(seconds=seconds), reason=причина)
        await interaction.followup.send(f"{участник.mention} замьючен на {время}. Причина: {причина or 'не указана'}", ephemeral=True)

        
        log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
        if log_channel:
            embed = discord.Embed(title="Мут пользователя", color=discord.Color.red())
            embed.add_field(name="Пользователь", value=участник.mention, inline=False)
            embed.add_field(name="Модератор", value=interaction.user.mention, inline=False)  # <- вот тут правильно
            embed.add_field(name="Причина", value=причина or "не указана", inline=False)
            embed.add_field(name="Длительность", value=время, inline=False)
            embed.timestamp = now
            embed.color = discord.Color.yellow()
            embed.set_footer(text={участник.id})
            embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
            await log_channel.send(content=f"<@640069373108813824>",embed=embed)

    except Exception as e: return await interaction.response.send_message(f"Error unknow: {str(e)}", ephemeral=True)

 #---UNMUTE---

 @app_commands.command(name="unmute", description="снять мут с пользователя")
 @app_commands.describe(участник="кого размьютить", причина="необязательно")
 @app_commands.allowed_contexts(guilds=True)
 async def unmute(self, interaction: discord.Interaction, участник: discord.Member, причина: str = None):
    await interaction.response.defer(ephemeral=True)
    if not interaction.user.guild_permissions.moderate_members: return await interaction.followup.send("У вас нет прав на использование этой команды.", ephemeral=True)
    now = datetime.now(timezone(timedelta(hours=3)))
    try:
        await участник.timeout(None, reason=причина)
        await interaction.followup.send(f"{участник.mention} размьючен. Причина: {причина or 'не указана'}", ephemeral=True)

        # Лог
        log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
        if log_channel:
            embed = discord.Embed(title="Размут", color=discord.Color.green())
            embed.add_field(name="Пользователь", value=участник.mention, inline=False)
            embed.add_field(name="Модератор", value=interaction.user.mention, inline=False)
            embed.add_field(name="Причина", value=причина or "не указана", inline=False)
            embed.timestamp = now
            embed.color = discord.Color.green()
            embed.set_footer(text={участник.id})
            embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
            await log_channel.send(content=f"<@640069373108813824>",embed=embed)

    except Exception as e: return await interaction.followup.send(f"Error unknow: {str(e)}", ephemeral=True)

 #---BAN---

 @app_commands.command(name="ban", description="забанить пользователя")
 @app_commands.describe(участник="кого забанить", причина="необязательно")
 @app_commands.allowed_contexts(guilds=True)
 async def ban(self, interaction: discord.Interaction, участник: discord.Member, время: str = None, причина: str = None):
    await interaction.response.defer(ephemeral=True)
    if not interaction.user.guild_permissions.ban_members: return await interaction.followup.send("У вас нет прав на использование этой команды.", ephemeral=True)
    if utils.is_protected(interaction, участник): return await interaction.followup.send("Данный пользователь защищён от модераторских воздействий.", ephemeral=True)
    now = datetime.now(timezone(timedelta(hours=3)))
    await участник.ban(reason=причина)
    await interaction.followup.send(f"{участник.mention} забанен. Причина: {причина or 'не указана'}", ephemeral=True)
        
    log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
    if log_channel:
        embed = discord.Embed(title="Бан пользователя", color=discord.Color.red())
        embed.add_field(name="Пользователь", value=участник.mention, inline=False)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=False)
        embed.add_field(name="Причина", value=причина or "не указана", inline=False)
        embed.timestamp = now
        embed.color = discord.Color.red()
        embed.set_footer(text={участник.id})
        embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        await log_channel.send(content=f"<@640069373108813824>",embed=embed)

 #---UNBAN---

 @app_commands.command(name="unban", description="разбанить пользователя")
 @app_commands.describe(пользователь="ID пользователя", причина="необязательно")
 @app_commands.allowed_contexts(guilds=True)
 async def unban(self, interaction: discord.Interaction, пользователь: str, причина: str = None):
    await interaction.response.defer(ephemeral=True)
    if not interaction.user.guild_permissions.ban_members: return await interaction.followup.send("У вас нет прав на использование этой команды.", ephemeral=True)
    now = datetime.now(timezone(timedelta(hours=3)))
    try:
        user = await self.bot.fetch_user(int(пользователь))
        await interaction.guild.unban(user, reason=причина)
        await interaction.followup.send(f"{user.mention} разбанен. Причина: {причина or 'не указана'}", ephemeral=True)

        # Лог
        log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
        if log_channel:
            embed = discord.Embed(title="Разбан", color=discord.Color.green())
            embed.add_field(name="Пользователь", value=f"{user.mention} (`{пользователь}`)", inline=False)
            embed.add_field(name="Модератор", value=interaction.user.mention, inline=False)
            embed.add_field(name="Причина", value=причина or "не указана", inline=False)
            embed.timestamp = now
            embed.color = discord.Color.green()
            embed.set_footer(text={пользователь})
            embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
            await log_channel.send(content=f"<@640069373108813824>",embed=embed)

    except Exception as e: return await interaction.followup.send(f"Error unknow: {str(e)}", ephemeral=True)
