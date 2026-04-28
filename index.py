import discord, asyncio
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from commands.moderation import Модерация
from commands.other import BlockDmCmd, BirthdayCmd, InvitesCmd, CloseDMView
from commands.user import gif, invite, purge_dm
from commands.session import session
from tickets.task import TaskCmd, TaskOrderCmd
from tickets.tickets_commands import Commands, Guides
from tools.start import build_activity_embed, build_activity_embed2, build_roles_embed2, build_roles_embed, birthday_checker, check_visa_expirations, change_status
from tools.messages import правила, инфо, лор, emc, tickets, tickets_for_tourist
from tickets.tickets import handle_ticket_select
from main import BOT
from tools.config import OWNER, GUILD_ID 

@BOT.event
async def on_ready():
    print(f"[DEBUG] Бот запущен как {BOT.user}")
    BOT.add_view(CloseDMView())
    try:
        #bot.tree.clear_commands(guild=discord.Object(id=GUILD_ID))
        await BOT.tree.sync(guild=discord.Object(id=GUILD_ID))                
        print("[DEBUG] Изменения применены.")
    except Exception as e: print(f"[DEBUG] Ошибка при синхронизации команд: {e}")
    await asyncio.gather(start_next_tick(), start_next_minute(), start_next_hour())


async def start_next_tick():
    activity = discord.Activity(type=discord.ActivityType.competing,name=f"работает в тестовом режиме")
    await BOT.change_presence(status=discord.Status.dnd, activity=activity)
    #now = datetime.now(timezone(timedelta(hours=3)))
    #await asyncio.sleep(10 - (now.second % 10) - now.microsecond / 1_000_000)
    #change_status.start()

async def start_next_minute():
    now = datetime.now(timezone(timedelta(hours=3)))
    await asyncio.sleep(60 - now.second - now.microsecond / 1_000_000)
    try: await tickets(), await emc(), await tickets_for_tourist(), check_visa_expirations.start(), await build_roles_embed(), await build_roles_embed2(), await build_activity_embed2(), await build_activity_embed()
    except Exception as e: print("Ошибка в start_update:", e)

async def start_next_hour():
    now = datetime.now(timezone(timedelta(hours=3)))
    await asyncio.sleep(3600 - (now.minute * 60 + now.second + now.microsecond / 1_000_000))
    birthday_checker.start()


#----EMBEDS----

@BOT.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component: return
    if interaction.data.get("custom_id") in ["ticket_select", "ticket_select_for_tourist"]:
        if interaction.data.get("values", [None])[0]: await handle_ticket_select(BOT, interaction, interaction.data.get("values", [None])[0])

@BOT.command(name="ping")
async def ping(ctx):
    await ctx.author.send("pong", view=CloseDMView())

@BOT.command(name="report_for_weeks")
async def test(ctx):
    if ctx.author.id not in OWNER:
        await ctx.send("У вас нет прав на использование этой команды.", ephemeral=True)
        return
    
    message_data = {
        "flags": 32768,
        "components": [
            {
                "type": 10,
                "content": "# <:Rr:1482040483109933108><:Ee:1482032733449490452><:Pp:1482039424043978773><:Oo:1482039075010777109><:Rr:1482040483109933108><:Tt:1482041115396935762>  <:Ff:1482033194986377437><:Oo:1482039075010777109><:Rr:1482040483109933108>  \n## <:11:1482830822456299601><:55:1482830975728619662>.<:00:1482830781251588159><:11:1482830822456299601> - <:11:1482830822456299601><:55:1482830975728619662>.<:00:1482830781251588159><:33:1482830894892060793>:\n-# по факту с момента начала активного развития города"
            },
            {
                "type": 14,
                "spacing": 2,
                "divider": True
            },
            {
                "type": 10,
                "content": "## <:Mm:1482037203529105489><:Aa:1482029767397081088><:Dd:1482031919074902028><:Ee:1482032733449490452>:\n> * собраны все ресурсы на основной остров\n> * приняты 4 жителя в город; 1 житель был кикнут\n> * город переехал на ЖВ900\n> * обновлена вся информация города\n> * у города появились первые фермы\n> * город стал способен обеспечивать себя базовыми вещами автономно за счёт текущих ферм\n> * сделано лого города (заказ)\n> * написана бета версия конституции ([тык](https://discord.com/channels/1341738075113390132/1375344169786146816/1470803122124492874))\n> * был доделан запасной рендер города ([тык](https://discord.com/channels/1341738075113390132/1375344169786146816/1475130037895430207)) (заказ)\n> * создан собственный шрифт города в дискорде (<:Aa:1482029767397081088><:Bb:1482030101574058054><:Cc:1482030661098406101>)"
            },
            {
                "type": 14,
                "spacing": 2,
                "divider": True
            },
            {
                "type": 10,
                "content": "## <:Ii:1482035492215062548><:Nn:1482038810006130869>  <:Pp:1482039424043978773><:Rr:1482040483109933108><:Oo:1482039075010777109><:Cc:1482030661098406101><:Ee:1482032733449490452><:Ss:1482040833132855328><:Ss:1482040833132855328>:\n> * перестройка основного острова\n> * проектирование ивента и первое строение\n> * продолжение написания собственного бота\n> * совсем скоро будет доделан основной рендер города (заказ)"
            },
            {
                "type": 14,
                "spacing": 2,
                "divider": True
            },
            {
                "type": 10,
                "content": "## <:Pp:1482039424043978773><:Ll:1482036746928787547><:Aa:1482029767397081088><:Nn:1482038810006130869><:Nn:1482038810006130869><:Ee:1482032733449490452><:Dd:1482031919074902028>:\n-# на ближайшие ~2 недели\n> * сбор ресурсов на первое строение, а потом ивент\n> * перестройка первого строения, а потом ивента\n> * развитие существующих ферм и создание новых по мере необходимости"
            }
        ]
    }
    
    await BOT.http.request(discord.http.Route("POST", "/channels/{channel_id}/messages", channel_id=1467685553549086804), json=message_data)


#@BOT.command(name="цом")
async def цвет(ctx):
    if ctx.author.id not in OWNER: return await ctx.send("У вас нет прав на использование этой команды.", ephemeral=True)
    await emc()

#@BOT.command(name="мфц1")
async def меню1(ctx):
    if ctx.author.id not in OWNER: return await ctx.send("У вас нет прав на использование этой команды.", ephemeral=True)
    #await tickets1()

#@BOT.command(name="мфц2")
async def меню2(ctx):
    if ctx.author.id not in OWNER:
        await ctx.send("У вас нет прав на использование этой команды.", ephemeral=True)
        return
    await tickets()

#@BOT.command(name="мфц_all")
async def меню3(ctx):
    if ctx.author.id not in OWNER:
        await ctx.send("У вас нет прав на использование этой команды.", ephemeral=True)
        return
    #await tickets1(bot)
    await tickets()

#@BOT.command(name="all") #+ emc
async def all_send(ctx):
    if ctx.author.id not in OWNER:
        await ctx.send("У вас нет прав на использование этой команды.", ephemeral=True)
        return
    await правила(ctx)
    await инфо(ctx)
    await лор(ctx)
    await emc()


#----COMMANDS----
BOT.tree.add_command(Модерация(), guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(BlockDmCmd(), guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(BirthdayCmd(), guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(InvitesCmd(), guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(gif, guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(invite, guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(purge_dm, guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(session, guild=discord.Object(id=GUILD_ID))
#----TICKETS----
BOT.tree.add_command(Commands(), guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(Guides(), guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(TaskCmd(), guild=discord.Object(id=GUILD_ID))
BOT.tree.add_command(TaskOrderCmd(), guild=discord.Object(id=GUILD_ID))