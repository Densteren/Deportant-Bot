import discord, requests, io, os, tempfile
from datetime import datetime, timezone, timedelta
from PIL import Image
from moviepy import VideoFileClip
from discord import app_commands
from tools.utils import is_time_formate, parse_time
from tools.config import GUILD_ID, LOG_COMMAND_CHANNEL

@app_commands.command(name="gif", description="Конвертирует изображение или короткое видео в gif")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(ссылка="Ссылка на изображение (jpg/png) или видео (mp4/webm)")
async def gif(interaction: discord.Interaction, ссылка: str):
    await interaction.response.defer(ephemeral=True)
    bot = interaction.client
    guild = bot.get_guild(GUILD_ID)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)

    try:
        response = requests.get(ссылка)
        response.raise_for_status()
        file_type = response.headers["Content-Type"]
        file_bytes = io.BytesIO(response.content)

        gif_buffer = io.BytesIO()

        if "image" in file_type:
            img = Image.open(file_bytes).convert("RGB")
            img.save(gif_buffer, format='GIF')
        elif "video" in file_type:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

                clip_full = None
                clip = None
                output_path = None
            try:
                clip_full = VideoFileClip(temp_file_path)
                clip = clip_full.subclip(0, min(3, clip_full.duration))
                output_path = temp_file_path.replace(".mp4", ".gif")
                clip.write_gif(output_path, program="ffmpeg")

                with open(output_path, "rb") as f:
                    gif_buffer = io.BytesIO(f.read())
            finally:
                if clip is not None:
                    clip.close()
                if clip_full is not None:
                    clip_full.close()
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if output_path and os.path.exists(output_path):
                    os.remove(output_path)
        else:
            raise ValueError("Формат не поддерживается")

        gif_buffer.seek(0)
        file = discord.File(fp=gif_buffer, filename="converted.gif")
        sent_message = await interaction.followup.send(file=file)

        # Логирование (как у тебя)
        gif_url = sent_message.attachments[0].url if sent_message.attachments else "Не удалось получить ссылку"
        log_channel = guild.get_channel(LOG_COMMAND_CHANNEL)
        if log_channel:
            log_text = discord.Embed(
                title="Использование команды",
                description=f"{interaction.user.mention} использовал `/gif {ссылка}` в {interaction.channel.mention}\n[Открыть GIF]({gif_url})",
                timestamp=now
            )
            log_text.set_footer(text=file_type)
            log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
            await log_channel.send(embed=log_text)

    except Exception as e:
        await interaction.followup.send(f"Произошла ошибка: `{e}`", ephemeral=True)

@app_commands.command(name="clear", description="удалить все сообщения бота в лс")
@app_commands.allowed_contexts(dms=True)
@app_commands.describe(аргумент="целое число или формат времени (`2m`, `3d`)")
async def purge_dm(interaction: discord.Interaction, аргумент: str):
    if not isinstance(interaction.channel, discord.DMChannel):
        return await interaction.response.send_message("Эту команду можно использовать только в личных сообщениях боту.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    
    is_time = is_time_formate(аргумент)
    if is_time:
        seconds = parse_time(аргумент)
        time = now - timedelta(seconds=seconds)
        if seconds is None:
            await interaction.followup.send("Неправильный аргумент: введите целое число без букв (например: `10`) или **формат времени** (`5m`, `2h`).", ephemeral=True)
            return
    else:
        try:
            amount = int(аргумент)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await interaction.followup.send("Неправильный аргумент: введите **целое число** без букв (например: `10`) или формат времени (`5m`, `2h`).", ephemeral=True)
            return
        
    deleted = 0
    bot = interaction.client
    guild = bot.get_guild(GUILD_ID)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    async for message in interaction.channel.history():
        if message.author == bot.user:
            try:
                if is_time and message.created_at > time:
                    await message.delete()
                    deleted += 1
                else:
                    await message.delete()
                    deleted += 1
                    if deleted >= amount:
                        break
    
            except Exception as e:
                await interaction.followup.send(f"Error unknow: {str(e)}", ephemeral=True)

    msg = f"Удалено сообщений бота: {deleted}"
    await interaction.followup.send(content=msg, ephemeral=True)
    log_channel = guild.get_channel(LOG_COMMAND_CHANNEL)
    if log_channel:
        log_text = discord.Embed(
            title="Использование команды",
            description=f"{interaction.user.mention} использовал `/clear` {аргумент}\n```{msg}```",
            timestamp=now
        )
        log_text.set_footer(text=deleted)
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        await log_channel.send(embed=log_text)
