
import discord
from discord.ext import commands
from tools.config import TOKEN
BOT = commands.Bot(command_prefix="kop!", intents=discord.Intents.all())
try: BOT.run(TOKEN)
except Exception as e: print(f"Ошибка: {e}"), input("Нажмите Enter, чтобы выйти...")