import discord
from tools.config import OWNER, GUILD_ID
from main import BOT
class EMCTicketsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Тикет в ЦОМ", custom_id=f"emc_tickets_button", disabled=True, style=discord.ButtonStyle.success)

    async def callback(self, interaction:discord.Interaction): pass
        
class EMCEventsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Расписание", style=discord.ButtonStyle.link, url="https://teamup.com/c/qurp36/deportant")
