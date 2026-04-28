import discord
from discord import app_commands
from datetime import datetime, timezone, timedelta
from storage import storage
from tickets.tickets import CloseView, MySelect
from storage.storage import tickets_info, block_tickets_users, guides_storage
from tools.utils import format_message_content
from tools.config import LOG_DEBUGS_CHANNEL, ADMIN_TICKET, GUIDE_ROLE, LOG_COMMAND_CHANNEL, OWNER_ROLE, OWNERS

class MyView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        self.add_item(MySelect(guild))

TICKET_TYPES = [
    app_commands.Choice(name="Заявка в город", value="act"),
    app_commands.Choice(name="Получение визы", value="ov"),
    app_commands.Choice(name="Связь с владельцем", value="co"),
    app_commands.Choice(name="Анонимная жалоба", value="ac"),
    app_commands.Choice(name="Другое", value="oth")
]

class Commands(app_commands.Group):
 def __init__(self): super().__init__(name="ticket", description="команды для работы с тикетами")
 
 @app_commands.command(name="close", description="закрыть тикет")
 @app_commands.describe(client="владелец тикет", value="тип проблемы тикета")
 @app_commands.allowed_contexts(guilds=False, dms=False, private_channels=True)
 @app_commands.choices(value=TICKET_TYPES)
 async def close_ticket(self, interaction: discord.Interaction, client: discord.Member, value: app_commands.Choice[str]):
     guild = interaction.guild
     msk = timezone(timedelta(hours=3))
     now = datetime.now(msk)
     #formatted_time = now.strftime("%d.%m.%y %H:%M")
     client_id = client.id
     client_idvalue = f"{client_id}-{value.value}"

     try:
        data = tickets_info.get(client_idvalue)
     except Exception as e:
        log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
        if log_channel:
            log_text = discord.Embed(
            title = "[DEBUG] Ошибка при поиске данных тикета",
            description = f"`{e}`\n`tickets.py:420`",
            color = discord.Color.red(),
            timestamp=now
            )
            log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
            #log_text.set_footer(text=F"{formatted_time}█")
        await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
        await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
        return
     
     channel = guild.get_channel(data["client_channel"])
     if interaction.channel != channel:
         await interaction.response.send_message("Данную команду можно использовать только в тикетах.", ephemeral=True)
         return
     role = guild.get_role(OWNER_ROLE)
     admin_ticket = guild.get_role(ADMIN_TICKET)

     if role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
        await interaction.response.send_message("Вы не имеете прав на закрывание тикета(ов).", ephemeral=True)
        return
     if value.value in ("co", "ac"):
         if interaction.user.id not in OWNERS:
             await interaction.response.send_message("Только владелец может закрыть данный тип тикета.", ephemeral=True)
             return
     
     await interaction.response.send_message("Вы уверены что хотите закрыть тикет? Открыть его будет невозможно!", view=CloseView(self.bot, client_id=client_id, value=value), ephemeral=True)

 @app_commands.command(name="add", description="закрыть тикет")
 @app_commands.describe(add="кого добавить", client="владелец тикет", value="тип проблемы тикета")
 @app_commands.allowed_contexts(guilds=False, dms=False, private_channels=True)
 @app_commands.choices(value=TICKET_TYPES)
 async def add_ticket(self, interaction: discord.Interaction, add: discord.Member, client: discord.Member, value: app_commands.Choice[str]):
     guild = interaction.guild
     msk = timezone(timedelta(hours=3))
     now = datetime.now(msk)
     #formatted_time = now.strftime("%d.%m.%y %H:%M")
     client_id = client.id
     client_idvalue = f"{client_id}-{value.value}"

     try:
        data = tickets_info.get(client_idvalue)
     except Exception as e:
        log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
        if log_channel:
            log_text = discord.Embed(
            title = "[DEBUG] Ошибка при поиске данных тикета",
            description = f"`{e}`\n`tickets.py:461`",
            color = discord.Color.red(),
            timestamp=now
            )
            log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
            #log_text.set_footer(text=F"{formatted_time}█")
        await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
        await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
        return

     channel = guild.get_channel(data["client_channel"])
     if interaction.channel != channel:
         await interaction.response.send_message("Данную команду можно использовать только в тикетах.", ephemeral=True)
         return
     
     role = guild.get_role(OWNER_ROLE)
     admin_ticket = guild.get_role(ADMIN_TICKET)

     if role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
        await interaction.response.send_message("Вы не имеете прав на добавление в тикет(ы).", ephemeral=True)
        return
     if value.value in ("co", "ac"):
         if interaction.user.id not in OWNERS:
             await interaction.response.send_message("Только владелец может добавлять в тикет данного типа.", ephemeral=True)
             return
     
     overwrites = channel.overwrites
     overwrites[add] = discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True)
     await channel.edit(overwrites=overwrites)

     result_msg = f"{add.mention} был добавлен в тикет"
     await interaction.response.send_message(content=result_msg, ephemeral=True)
     await channel.send(f"{interaction.user.mention} добавил в тикет {add.mention}.", delete_after=60)

     log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
     view_log = discord.ui.View()
     view_log.add_item(discord.ui.Button(
            label="Перейти в канал",
            style=discord.ButtonStyle.link,
            url=channel.jump_url))
     if log_channel:
        log_text = discord.Embed(
        title = "Добавление в тикет",
        description = f"{interaction.user.mention} использовал `/ticket add {add} {client} {value}` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.green(),
        timestamp=now
        )
        log_text.set_footer(text={channel.id})
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        await log_channel.send(embed=log_text, view=view_log)

 @app_commands.command(name="remove", description="удалить пользователя из тикета")
 @app_commands.describe(remove="кого удалить", client="владелец тикета", value="тип проблемы тикета")
 @app_commands.allowed_contexts(guilds=False, dms=False, private_channels=True)
 @app_commands.choices(value=TICKET_TYPES)
 async def remove_ticket(self, interaction: discord.Interaction, remove: discord.Member, client: discord.Member, value: app_commands.Choice[str]):
    guild = interaction.guild
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    #formatted_time = now.strftime("%d.%m.%y %H:%M")
    client_idvalue = f"{client.id}-{value.value}"

    try:
        data = tickets_info.get(client_idvalue)
    except Exception as e:
        log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
        if log_channel:
            log_text = discord.Embed(
            title = "[DEBUG] Ошибка при поиске данных тикета",
            description = f"`{e}`\n`tickets.py:507`",
            color = discord.Color.red(),
            timestamp=now
            )
            log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
            #log_text.set_footer(text=F"{formatted_time}█")
        await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
        await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
        return

    channel = guild.get_channel(data["client_channel"])
    if interaction.channel != channel:
        await interaction.response.send_message("Данную команду можно использовать только в тикетах.", ephemeral=True)
        return

    role = guild.get_role(OWNER_ROLE)
    admin_ticket = guild.get_role(ADMIN_TICKET)

    if role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
        await interaction.response.send_message("Вы не имеете прав на удаление из тикета(ов).", ephemeral=True)
        return
    if value.value in ("co", "ac"):
         if interaction.user.id not in OWNERS:
             await interaction.response.send_message("Только владелец может удалять из тикета данного типа.", ephemeral=True)
             return

    overwrites = channel.overwrites
    if remove in overwrites:
        del overwrites[remove]
        await channel.edit(overwrites=overwrites)

        result_msg = f"{remove.mention} был удалён из тикета."
        await interaction.response.send_message(content=result_msg, ephemeral=True)
        await channel.send(f"{interaction.user.mention} удалил из тикета {remove.mention}.", delete_after=60)

        log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
        view_log = discord.ui.View()
        view_log.add_item(discord.ui.Button(
            label="Перейти в канал",
            style=discord.ButtonStyle.link,
            url=channel.jump_url))
        if log_channel:
            log_text = discord.Embed(
            title = "Удаление из тикета",
            description = f"{interaction.user.mention} использовал `/ticket remove {remove} {client} {value}` в {interaction.channel.mention}\n```{result_msg}```",
            color = discord.Color.yellow(),
            timestamp=now
            )
            log_text.set_footer(text={channel.id})
            log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
            await log_channel.send(embed=log_text, view=view_log)

 @app_commands.command(name="block", description="запретить пользователю создавать тикеты")
 @app_commands.describe(user="пользователь, которому запретить")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def block_ticket(self, interaction: discord.Interaction, user: discord.User):
    if user.id not in block_tickets_users:
        block_tickets_users.add(user.id)
        storage.save_bl_ti_us(block_tickets_users)
        result_msg = f"Пользователь {user.mention} заблокирован в ЛС."
    else:
        result_msg = "Этот пользователь уже заблокирован."
    await interaction.response.send_message(content=result_msg, ephemeral=True)

    log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
    if log_channel:
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        log_text = discord.Embed(
        title = "Добавление в блок",
        description = f"{interaction.user.mention} использовал `/ticket block {user}` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.yellow(),
        timestamp=now
        )
        log_text.set_footer(text={user.id})
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        await log_channel.send(embed=log_text)

 @app_commands.command(name="unblock", description="разрешить пользователю создавать тикеты")
 @app_commands.describe(user="пользователь, которому разрешить")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def unblock_ticket(self, interaction: discord.Interaction, user: discord.User):
    if user.id in block_tickets_users:
        block_tickets_users.remove(user.id)
        storage.save_bl_ti_us(block_tickets_users)
        result_msg = f"{user.mention} разблокирован."
    else:
        result_msg = "Этот пользователь не был заблокирован."
    await interaction.response.send_message(content=result_msg, ephemeral=True)
    
    log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
    if log_channel:
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        log_text = discord.Embed(
        title = "Удаление из блока",
        description = f"{interaction.user.mention} использовал `/ticket unblock {user}` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.red(),
        timestamp=now
        )
        log_text.set_footer(text={user.id})
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        await log_channel.send(embed=log_text)

 @app_commands.command(name="reset_tickets", description="сбросить счётчики тикетов")
 @app_commands.allowed_contexts(guilds=False, dms=False, private_channels=True)
 async def reset_tickets(self, interaction: discord.Interaction):
     guild = interaction.guild
     owner_role = guild.get_role(OWNER_ROLE)

     if owner_role not in interaction.user.roles and not interaction.user.id in OWNERS:
         await interaction.response.send_message("Только владелец может использовать эту команду.", ephemeral=True)
         return

     storage.reset_ticket_counters()
     await interaction.response.send_message("Счётчики тикетов успешно сброшены.", ephemeral=True)

class Guides(app_commands.Group):
 def __init__(self): super().__init__(name="guides", description="команды для работы с списком гидов")
 
 @app_commands.command(name="add", description="добавить гида")
 @app_commands.describe(user="новый гид")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def add_guides(self, interaction: discord.Interaction, user: discord.User):
     guild = interaction.guild
     owner_role = guild.get_role(OWNER_ROLE)
     guide_role = guild.get_role(GUIDE_ROLE)

     if owner_role not in interaction.user.roles and interaction.user.id not in OWNERS:
        await interaction.response.send_message("Вы не имеете прав на добавление в список.", ephemeral=True)
        return
     if user.id not in guides_storage:
        guides_storage.add(user.id)
        storage.save_guides(guides_storage)
        member = guild.get_member(user.id)
        await member.add_roles(guide_role, reason="Добавлен в список гидов через команду бота")
        result_msg = f"Пользователь {user.mention} добавлен в список и получил роль **{guide_role.mention}**."
     else:
        result_msg = "Этот пользователь уже в списке."
     await interaction.response.send_message(content=result_msg, ephemeral=True)

     log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
     msk = timezone(timedelta(hours=3))
     now = datetime.now(msk)
     if log_channel:
        log_text = discord.Embed(
        title = "Добавление гида",
        description = f"{interaction.user.mention} использовал `/guides add {user.mention}` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.green(),
        timestamp=now
        )
        log_text.set_footer(text={user.id})
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        await log_channel.send(embed=log_text)

 @app_commands.command(name="list", description="список гидов")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def list_guides(self, interaction: discord.Interaction):
    guild = interaction.guild

    lines = []
    guides_storage = storage.load_guides()
    if not guides_storage:
        await interaction.response.send_message("Список гидов пуст.", ephemeral=True)
        return
    for user_id in guides_storage:
        user = guild.get_member(user_id)
        if not user:
            try:
                user = await guild.fetch_member(user_id)
            except (discord.NotFound, discord.Forbidden):
                user = None
        if user:
            lines.append(f"• {user.mention} (`{user.id}`)")
        else:
            lines.append(f"• <@&{user_id}> (удален или недоступен)")

    text = "\n".join(lines)
    embed = discord.Embed(
        description=f"### Список гидов:\n{text}"
    )
    msg = await interaction.response.send_message(embed=embed, ephemeral=True)
    result_msg = format_message_content(msg)

    log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    if log_channel:
        log_text = discord.Embed(
        title = "Просмотр списка гидов",
        description = f"{interaction.user.mention} использовал `/guides list` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.yellow(),
        timestamp=now
        )
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        await log_channel.send(embed=log_text)

 @app_commands.command(name="remove", description="убрать гида")
 @app_commands.describe(user="кого увольняем")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 async def remove_guides(self, interaction: discord.Interaction, user: discord.User):
     guild = interaction.guild
     owner_role = guild.get_role(OWNER_ROLE)
     guide_role = guild.get_role(GUIDE_ROLE)

     if owner_role not in interaction.user.roles and interaction.user.id not in OWNERS:
        await interaction.response.send_message("Вы не имеете прав на удаление из списка.", ephemeral=True)
        return
     if user.id in guides_storage:
        guides_storage.remove(user.id)
        storage.save_guides(guides_storage)
        member = guild.get_member(user.id)
        await member.remove_roles(guide_role, reason="Убран из списка гидов через команду бота")
        result_msg = f"Пользователь {user.mention} убран из списка и потерял роль **{guide_role.name}**."
     else:
        result_msg = "Этого пользователя не было в списке."
     await interaction.response.send_message(content=result_msg, ephemeral=True)
    
     log_channel = interaction.guild.get_channel(LOG_COMMAND_CHANNEL)
     msk = timezone(timedelta(hours=3))
     now = datetime.now(msk)
     if log_channel:
        log_text = discord.Embed(
        title = "Удаление из списка гидов",
        description = f"{interaction.user.mention} использовал `/guides remove {user}` в {interaction.channel.mention}\n```{result_msg}```",
        color = discord.Color.red(),
        timestamp=now
        )
        log_text.set_footer(text={user.id})
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        await log_channel.send(content="<@640069373108813824>", embed=log_text)
