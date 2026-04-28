import discord
from discord import app_commands
from datetime import datetime, timezone, timedelta
from storage.storage import task_info
from tools.config import TACK_ROLES, TASK_CHANNEL, TASK_REESTR, LOG_COMMAND_CHANNEL, OWNERS, CUSTOM_TASK_ROLES, ADMIN_TICKET, LOG_DEBUGS_CHANNEL
from storage import storage
from tools.utils import generate_random_id, format_message_content
TEST_MODE = True

COMPLEXITY_TYPES = [
    app_commands.Choice(name="🟩 Легко", value="🟩🟩🟩🟩🟩"),
    app_commands.Choice(name="🟨 Средне", value="🟨🟨🟨🟨🟨"),
    app_commands.Choice(name="🟧 Сложно", value="🟧🟧🟧🟧🟧"),
    app_commands.Choice(name="🟥 Очень сложно", value="🟥🟥🟥🟥🟥"),
    app_commands.Choice(name="⬛ Адски сложно", value="⬛⬛⬛⬛⬛")]

class TaskView(discord.ui.View):
    def __init__(self, random_id):
        super().__init__(timeout=None)
        self.add_item(TaskClaimButton(random_id))

    def claim_task(self, name, channel):
        self.clear_items()  # убираем все кнопки
        self.add_item(
            discord.ui.Button(
                label="Принять задание",
                style=discord.ButtonStyle.green,
                disabled=True
            )
        )
        self.add_item(
            discord.ui.Button(
                label=f"{name}",
                style=discord.ButtonStyle.gray,
                disabled=True
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Перейти в канал",
                style=discord.ButtonStyle.link,
                url=channel
            )
        )
        return self
    
    def end_task(self, name):
        self.clear_items()  # убираем все кнопки
        self.add_item(
            discord.ui.Button(
                label=f"Выполнил {name}",
                style=discord.ButtonStyle.green,
                disabled=True
            )
        )
        return self

class TaskTicketView(discord.ui.View):
    def __init__(self, random_id):
        super().__init__(timeout=None)
        self.add_item(TaskCompliteButton(random_id))
        self.add_item(TaskDeclineButton(random_id))

    def accepting_complite_task(self, random_id):
        self.clear_items()  # убираем все кнопки
        #self.add_item(discord.ui.Button(random_id))
        self.add_item(
            discord.ui.Button(
                label=f"Заглушка",
                style=discord.ButtonStyle.gray,
                disabled=True
            )
        )
        return self
    
    def accepting_decline_task(self, random_id):
        self.clear_items()  # убираем все кнопки
        #self.add_item(discord.ui.Button(random_id))
        self.add_item(
            discord.ui.Button(
                label=f"Заглушка",
                style=discord.ButtonStyle.gray,
                disabled=True
            )
        )
        return self


class TaskCmd(app_commands.Group):
 def __init__(self): super().__init__(name="task", description="команды для задач")

 @app_commands.command(name="create",description="cоздать задание(роль)")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 @app_commands.describe(task_mem="описание задачи", ping_mem="пинг тех кому предназначена задача", complexity="сложность/срочность", image_mem="url изображения", duration="срок(в днях(например: `5`, `2`))")
 @app_commands.choices(complexity=COMPLEXITY_TYPES)
 async def task_create_role(self, interaction: discord.Interaction,
    task_mem: str,
    ping_mem: discord.Role,
    complexity: app_commands.Choice[str],
    image_mem: str = "none",
    duration: int = None):

    #if interaction.user.id not in config.owner:
    #    return await interaction.response.send_message("Эта функция временно доступна только бета-тестерам.", ephemeral=True)
    
    for role in interaction.user.roles:
        allowed_ping = TACK_ROLES.get(role.id)
        if allowed_ping and ping_mem.id in allowed_ping or interaction.user.id in OWNERS:
            break
    else:
        await interaction.response.send_message("Эту роль вам нельзя выбрать.", ephemeral=True)

    guild = interaction.guild
    channel = guild.get_channel(TASK_CHANNEL)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    end_time = "Отсутствуют"
    expiration_iso = None
    color=discord.Color.green()
    random_id = generate_random_id()
    
    if duration is not None:
        delta = timedelta(minutes=duration) if TEST_MODE else timedelta(days=duration)
        expiration_date = datetime.now(msk) + delta
        expiration_iso = expiration_date.isoformat()
        end_time = f"<t:{int(expiration_date.timestamp())}:F>"
        color=discord.Color.yellow()
        
    embed = discord.Embed(
        title=f"Задача № `{random_id}`",
        description=f"{task_mem}\n\nСложность: {complexity.value}\nСроки: {end_time}",
        color=color,
        timestamp=now
    )
    embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
    if image_mem and image_mem != "none": embed.set_image(url=f"{image_mem}")
    view = TaskView(random_id)
    msg = await channel.send(content=f"{ping_mem.mention}", embed=embed, view=view)

    view_log = discord.ui.View()
    view_log.add_item(
        discord.ui.Button(
            label="Перейти к сообщению",
            style=discord.ButtonStyle.link,
            url=msg.jump_url
        )
    )
    await interaction.response.send_message("Задача создана!", view=view_log, ephemeral=True)

    #Логирование
    log_channel = guild.get_channel(TASK_REESTR)
    if log_channel:
        log_text = discord.Embed(
        title = f"Задача № {random_id}",
        description = f"{task_mem}\n\nСложность: {complexity.value}\nСроки: {end_time}\n```Статус задачи: ACTIVE```",
        color = discord.Color.green(),
        timestamp=now
        )
        if image_mem and image_mem != "none": log_text.set_image(url=f"{image_mem}")
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        msg_re = await log_channel.send(embed=log_text, view=view_log)

    task_info[random_id] = {
            "status": "ACTIVE",
            "type": "CITY-ROLE", #CUSTOM
            "reestr_id": msg_re.id,
            "customer_id": interaction.user.id,
            "msg_id": msg.id,
            "task_mem": task_mem,
            "complexity": complexity.value,
            "image_mem": image_mem,
            "duration": expiration_iso,
            "ping_mem": ping_mem.id
        }
    storage.save_ts_in(task_info)

    content = format_message_content(msg)
    log_channel1 = guild.get_channel(LOG_COMMAND_CHANNEL)
    if log_channel1:
        log_text1 = discord.Embed(
        title = "Создание общего задания",
        description = f"{interaction.user.mention} использовал `/task create {ping_mem.mention}` в {interaction.channel.mention}\n{content}",
        color = discord.Color.yellow()
        )
        await log_channel1.send(embed=log_text1)

 @app_commands.command(name="create_personal",description="cоздать задание(игрок)")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 @app_commands.describe(task_mem="описание задачи", ping_mem="пинг того кому предназначена задача", complexity="сложность/срочность", image_mem="url изображения", duration="срок(в днях(например: `5`, `2`))")
 @app_commands.choices(complexity=COMPLEXITY_TYPES)
 async def task_create_user(self, interaction: discord.Interaction,
    task_mem: str,
    ping_mem: discord.Member,
    complexity: app_commands.Choice[str],
    duration: int,
    image_mem: str = "none"):

    #if interaction.user.id not in config.owner:
    #    return await interaction.response.send_message("Эта функция временно доступна только бета-тестерам.", ephemeral=True)
    
    guild = interaction.guild
    channel = guild.get_channel(TASK_CHANNEL)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    end_time = "Отсутствуют"
    expiration_iso = None
    color=discord.Color.green()
    random_id = generate_random_id()
    
    if duration is not None:
        delta = timedelta(minutes=duration) if TEST_MODE else timedelta(days=duration)
        expiration_date = datetime.now(msk) + delta
        expiration_iso = expiration_date.isoformat()
        end_time = f"<t:{int(expiration_date.timestamp())}:F>"
        color=discord.Color.yellow()
        
    embed = discord.Embed(
        title=f"Задача № `{random_id}`",
        description=f"{task_mem}\n\nСложность: {complexity.value}\nСроки: {end_time}",
        color=color,
        timestamp=now
    )
    embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
    if image_mem and image_mem != "none": embed.set_image(url=f"{image_mem}")
    view = TaskView(random_id)
    msg = await channel.send(content=f"{ping_mem.mention}", embed=embed, view=view)

    view_log = discord.ui.View()
    view_log.add_item(
        discord.ui.Button(
            label="Перейти к сообщению",
            style=discord.ButtonStyle.link,
            url=msg.jump_url
        )
    )
    await interaction.response.send_message("Задача создана!", view=view_log, ephemeral=True)

    #Логирование
    log_channel = guild.get_channel(TASK_REESTR)
    if log_channel:
        log_text = discord.Embed(
        title = f"Задача № {random_id}",
        description = f"{task_mem}\n\nСложность: {complexity.value}\nСроки: {end_time}\n```Статус задачи: ACTIVE```",
        color = discord.Color.green(),
        timestamp=now
        )
        if image_mem and image_mem != "none": log_text.set_image(url=f"{image_mem}")
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        msg_re = await log_channel.send(embed=log_text, view=view_log)

    task_info[random_id] = {
            "status": "ACTIVE",
            "type": "CITY-USER", #CUSTOM
            "reestr_id": msg_re.id,
            "customer_id": interaction.user.id,
            "msg_id": msg.id,
            "task_mem": task_mem,
            "complexity": complexity.value,
            "image_mem": image_mem,
            "duration": expiration_iso,
            "ping_mem": ping_mem.id
        }
    storage.save_ts_in(task_info)

    content = format_message_content(msg)
    log_channel = guild.get_channel(LOG_COMMAND_CHANNEL)
    if log_channel:
        log_text = discord.Embed(
        title = "Создание персонального задания",
        description = f"{interaction.user.mention} использовал `/task create_personal {ping_mem.mention}` в {interaction.channel.mention}\n{content}",
        color = discord.Color.yellow()
        )
        await log_channel.send(content=f"<@640069373108813824>",embed=log_text)

class TaskOrderCmd(app_commands.Group):
 def __init__(self): super().__init__(name="order", description="команды для задач")
 
 @app_commands.command(name="create",description="cоздать заказное задание задание")
 @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
 @app_commands.describe(task_mem="описание задачи", ping_mem="пинг тех кому предназначена задача", complexity="вознаграждение", image_mem="url изображения", duration="срок(в днях(например: `5`, `2`))")
 async def task_create_custom(self, interaction: discord.Interaction,
    task_mem: str,
    ping_mem: discord.Role,
    complexity: str,
    image_mem: str = "none",
    duration: int = None):
    
    guild = interaction.guild
    #custom_role = guild.get_role(1359589878085456074)
    #if custom_role not in interaction.user.roles and interaction.user.id not in config.owner:
    #    return await interaction.response.send_message("Эта функция временно доступна только `Deportant's partner`.", ephemeral=True)

    for role in interaction.user.roles:
        allowed_ping = CUSTOM_TASK_ROLES.get(role.id)
        if allowed_ping and ping_mem.id in allowed_ping:
            break
    else:
        await interaction.response.send_message("Эту роль вам нельзя выбрать.", ephemeral=True)
    
    channel = guild.get_channel(TASK_CHANNEL)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    end_time = "Отсутствуют"
    expiration_iso = None
    color=discord.Color.green()
    random_id = generate_random_id()
    
    if duration is not None:
        delta = timedelta(minutes=duration) if TEST_MODE else timedelta(days=duration)
        expiration_date = datetime.now(msk) + delta
        expiration_iso = expiration_date.isoformat()
        end_time = f"<t:{int(expiration_date.timestamp())}:F>"
        color=discord.Color.yellow()
        
    embed = discord.Embed(
        title=f"Задача № `{random_id}`",
        description=f"{task_mem}\n\nВознаграждение: {complexity}\nСроки: {end_time}",
        color=color,
        timestamp=now
    )
    embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
    if image_mem and image_mem != "none": embed.set_image(url=f"{image_mem}")
    view = TaskView(random_id)
    msg = await channel.send(content=f"{ping_mem.mention}", embed=embed, view=view)

    view_log = discord.ui.View()
    view_log.add_item(
        discord.ui.Button(
            label="Перейти к сообщению",
            style=discord.ButtonStyle.link,
            url=msg.jump_url
        )
    )
    await interaction.response.send_message("Задача создана!", view=view_log, ephemeral=True)

    #Логирование
    log_channel = guild.get_channel(TASK_REESTR)
    if log_channel:
        log_text = discord.Embed(
        title = f"Задача № {random_id}",
        description = f"{task_mem}\n\nВознаграждение: {complexity}\nСроки: {end_time}\n```Статус задачи: ACTIVE```",
        color = color,
        timestamp=now
        )
        if image_mem and image_mem != "none": log_text.set_image(url=f"{image_mem}")
        log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
    msg_re = await log_channel.send(embed=log_text, view=view_log)

    task_info[random_id] = {
            "status": "ACTIVE",
            "type": "CUSTOM", #CITY-ROLE(-USER)
            "reestr_id": msg_re.id,
            "customer_id": interaction.user.id,
            "msg_id": msg.id,
            "task_mem": task_mem,
            "complexity": complexity,
            "image_mem": image_mem,
            "duration": expiration_iso,
            "ping_mem": ping_mem.id
        }
    storage.save_ts_in(task_info)

    content = format_message_content(msg)
    log_channel = guild.get_channel(LOG_COMMAND_CHANNEL)
    if log_channel:
        log_text = discord.Embed(
        title = "Создание заказного задания",
        description = f"{interaction.user.mention} использовал `/order create {ping_mem.mention}` в {interaction.channel.mention}\n{content}",
        color = discord.Color.yellow()
        )
        await log_channel.send(content=f"<@640069373108813824>",embed=log_text)

class TaskClaimButton(discord.ui.Button):
    def __init__(self, random_id: str):
        super().__init__(label="Принять задание", style=discord.ButtonStyle.green, custom_id=f"ts_cl_button:{random_id}")
        self.random_id = random_id

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        task_info1 = storage.load_ts_in()
        task = task_info1.get(self.random_id)
        type_task = task["type"]
        reestr_id = task["reestr_id"]
        customer_id = task["customer_id"]
        customer = guild.get_member(customer_id)
        msg_id = task["msg_id"]
        task_mem = task["task_mem"]
        complexity = task["complexity"]
        image_mem = task["image_mem"]
        expiration_iso = task["duration"]
        role = None
        user = None
        if type_task == "CITY-ROLE":
            role = guild.get_role(task["ping_mem"])
        elif type_task == "CITY-USER":
            user = guild.get_member(task["ping_mem"])
        end_time = "Отсутствуют"
        if expiration_iso is not None:
            expiration_date = datetime.fromisoformat(expiration_iso)
            end_time = f"<t:{int(expiration_date.timestamp())}:F>"
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        admin_ticket = guild.get_role(ADMIN_TICKET)
        channel_name = f"⌛・task-for-{interaction.user.name}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            admin_ticket: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True),
            interaction.user: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True),
            customer: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True)
        }
        
        if role:
            if role not in interaction.user.roles:
                return await interaction.response.send_message(f"Это задание могут принять те, у кого есть роль {role.mention}", ephemeral=True)
        elif user:
            if user.id != interaction.user.id:
                return await interaction.response.send_message(f"Это задание может принять только {user.mention}", ephemeral=True)

        try:
            category = discord.utils.get(guild.categories, id=1453569406457090159)
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при поиске категории",
                description = f"`{e}`\n`tickets.py:326`",
                color = discord.Color.red(),
                timestamp=now
                )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            category = None
            pass

        color = discord.Color.green()
        if end_time and end_time != "Отсутствуют":
            color = discord.Color.yellow()
        channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites, category=category, topic=f"{self.random_id}")
        if type_task == "CUSTOM":
            embed = discord.Embed(
                title=f"Задача № `{self.random_id}`",
                description=f"{task_mem}\n\nВознаграждение: {complexity}\nСроки: {end_time}",
                color=color,
                timestamp=now
                )
        elif type_task == "CITY-ROLE" or "CITY-USER":
            embed = discord.Embed(
                title=f"Задача № `{self.random_id}`",
                description=f"{task_mem}\n\nСложность: {complexity}\nСроки: {end_time}",
                color=color,
                timestamp=now
                )
        embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        if image_mem and image_mem != "none": embed.set_image(url=f"{image_mem}")
    
        view=TaskTicketView(self.random_id)
        message = await channel.send(content=f"{interaction.user.mention}", embed=embed, view=view)
        task_info[self.random_id].update( {
                "status": "CLAIMED",
                "client_id": interaction.user.id,
                "channel_id": channel.id,
                "channel_msg_id": message.id
        })
        storage.save_ts_in(task_info)
        view_log = discord.ui.View()
        view_log.add_item(discord.ui.Button(
                label="Перейти в канал",
                style=discord.ButtonStyle.link,
                url=channel.jump_url))
        await interaction.response.send_message(f"Задача принята", ephemeral=True, view=view_log)
        channel1 = guild.get_channel(TASK_CHANNEL)
        viewnone = TaskView(self.random_id)
        view2 = viewnone.claim_task(name=interaction.user.name, channel=channel.jump_url)
        msg = await channel1.fetch_message(msg_id)
        msg.embeds[0].timestamp = now
        await msg.edit(embed=msg.embeds[0], view=view2)
    
        #Логирование
        log_channel = guild.get_channel(TASK_REESTR)
        if log_channel:
            if type_task == "CUSTOM":
                log_text = discord.Embed(
                title = f"Задача № {self.random_id}",
                description = f"{task_mem}\n\nВознаграждение: {complexity}\n Сроки: {end_time}\n```Статус задачи: CLAIMED```\n-# by {interaction.user.mention} ({interaction.user.id})",
                color = discord.Color.green(),
                timestamp=now
                )
            if type_task == "CITY-ROLE" or "CITY-USER":
                log_text = discord.Embed(
                title = f"Задача № {self.random_id}",
                description = f"{task_mem}\n\nСложность: {complexity}\n Сроки: {end_time}\n```Статус задачи: CLAIMED```\n-# by {interaction.user.mention} ({interaction.user.id})",
                color = discord.Color.green(),
                timestamp=now
                )
            if image_mem and image_mem != "none": log_text.set_image(url=f"{image_mem}")
            log_text.set_author(name=f"{customer.display_name} ({customer_id})", icon_url=customer.display_avatar.url)
        reestr_msg = await log_channel.fetch_message(reestr_id)
        await reestr_msg.edit(embed=log_text, view=view_log)

class TaskDeclineButton(discord.ui.Button):
    def __init__(self, random_id: str):
        super().__init__(label="Отказаться от задания", style=discord.ButtonStyle.red, custom_id=f"ts_dc_button:{random_id}")
        self.random_id = random_id

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel1 = guild.get_channel(TASK_CHANNEL)
        log_channel = guild.get_channel(TASK_REESTR)
        task_info1 = storage.load_ts_in()
        task = task_info1.get(self.random_id)
        type_task = task["type"]
        reestr_id = task["reestr_id"]
        reestr_msg = await log_channel.fetch_message(reestr_id)
        customer_id = task["customer_id"]
        customer = guild.get_member(customer_id)
        msg_id = task["msg_id"]
        msg = await channel1.fetch_message(msg_id)
        task_mem = task["task_mem"]
        complexity = task["complexity"]
        image_mem = task["image_mem"]
        expiration_iso = task["duration"]
        client_id = task["client_id"]
        #client = guild.get_member(client_id)
        channel_id = task["channel_id"]
        channel = guild.get_channel(channel_id)
        channel_msg_id = task["channel_msg_id"]
        channel_msg = await channel.fetch_message(channel_msg_id)
        end_time = "Отсутствуют"
        if expiration_iso is not None:
            expiration_date = datetime.fromisoformat(expiration_iso)
            end_time = f"<t:{int(expiration_date.timestamp())}:F>"
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        admin_ticket = guild.get_role(ADMIN_TICKET)
        channel_name = f"・task-for-{interaction.user.name}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            admin_ticket: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True),
            customer: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True)
        }
            
        if interaction.user.id != client_id:
            return await interaction.response.send_message("Отказаться от задания может только тот кто принял задание.", ephemeral=True)
        
        if type_task == "CITY-USER":
            return await interaction.response.send_message("Вы не можете отказаться от своего персонального задания", ephemeral=True)
        
        try:
            category = discord.utils.get(guild.categories, id=1376938513609654292)
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при поиске категории",
                description = f"`{e}`\n`tickets.py:326`",
                color = discord.Color.red(),
                timestamp=now
                )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            category = None
            pass

        await channel.edit(name=channel_name, overwrites=overwrites, category=category)
        viewnone = TaskTicketView(self.random_id)
        view1 = viewnone.accepting_decline_task(self.random_id)
        channel_msg.embeds[0].timestamp = now
        await channel_msg.edit(embed=msg.embeds[0], view=view1)
        await reestr_msg.delete()
        await interaction.response.send_message(f"Вы отказались от задачи", ephemeral=True)

        view2 = TaskView(self.random_id)
        msg.embeds[0].timestamp = now
        await msg.edit(embed=msg.embeds[0], view=view2)
    
        #Логирование
        view_log = discord.ui.View()
        view_log.add_item(discord.ui.Button(
                label="Перейти к сообщению",
                style=discord.ButtonStyle.link,
                url=msg.jump_url))
        if log_channel:
            if type_task == "CUSTOM":
                log_text = discord.Embed(
                title = f"Задача № {self.random_id}",
                description = f"{task_mem}\n\nВознаграждение: {complexity}\n Сроки: {end_time}\n```Статус задачи: ACTIVE```",
                color = discord.Color.green(),
                timestamp=now
                )
            elif type_task == "CITY-ROLE" or "CITY-USER":
                log_text = discord.Embed(
                title = f"Задача № {self.random_id}",
                description = f"{task_mem}\n\nСложность: {complexity}\n Сроки: {end_time}\n```Статус задачи: ACTIVE```",
                color = discord.Color.green(),
                timestamp=now
                )
            if image_mem and image_mem != "none": log_text.set_image(url=f"{image_mem}")
            log_text.set_author(name=f"{customer.display_name} ({customer_id})", icon_url=customer.display_avatar.url)
        reestr_msg = await log_channel.send(embed=log_text, view=view_log)

        task_info[self.random_id].update( {
                "status": "ACTIVE",
                "reestr_id": reestr_msg.id
        })
        task_info[self.random_id].pop("client_id", None)
        task_info[self.random_id].pop("channel_id", None)
        task_info[self.random_id].pop("channel_msg_id", None)
        storage.save_ts_in(task_info)

class TaskCompliteButton(discord.ui.Button):
    def __init__(self, random_id: str):
        super().__init__(label="Задание выполнено", style=discord.ButtonStyle.green, custom_id=f"ts_cm_button:{random_id}")
        self.random_id = random_id

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel1 = guild.get_channel(TASK_CHANNEL)
        log_channel = guild.get_channel(TASK_REESTR)
        task_info1 = storage.load_ts_in()
        task = task_info1.get(self.random_id)
        type_task = task["type"]
        reestr_msg = await log_channel.fetch_message(task["reestr_id"])
        customer = guild.get_member(task["customer_id"])
        msg = await channel1.fetch_message(task["msg_id"])
        task_mem = task["task_mem"]
        complexity = task["complexity"]
        image_mem = task["image_mem"]
        expiration_iso = task["duration"]
        client = guild.get_member(task["client_id"])
        channel = guild.get_channel(task["channel_id"])
        channel_msg = await channel.fetch_message(task["channel_msg_id"])
        end_time = "Отсутствуют"
        if expiration_iso is not None:
            expiration_date = datetime.fromisoformat(expiration_iso)
            end_time = f"<t:{int(expiration_date.timestamp())}:F>"
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
            
        if interaction.user.id != client.id:
            return await interaction.response.send_message("Сообщить о выполнении может только тот кто принял задание.", ephemeral=True)

        viewnone = TaskTicketView(self.random_id)
        view2 = viewnone.accepting_complite_task(self.random_id)
        channel_msg.embeds[0].timestamp = now
        await channel_msg.edit(embed=msg.embeds[0], view=view2)
        await interaction.response.send_message(f"Вы сообщили о выполнении задача", ephemeral=True)
        await channel.send(f"{customer.mention}, {client.mention} выполнил задачу")

        view_log = discord.ui.View()
        view_log.add_item(discord.ui.Button(
            label="Перейти в канал",
            style=discord.ButtonStyle.link,
            url=channel.jump_url))    
        if type_task == "CUSTOM":
            log_text = discord.Embed(
            title = f"Задача № {self.random_id}",
            description = f"{task_mem}\n\nВознаграждение: {complexity}\n Сроки: {end_time}\n```Статус задачи: COMPLITE ?```",
            color = discord.Color.green(),
            timestamp=now
            )
        elif type_task == "CITY-ROLE" or "CITY-USER":
            log_text = discord.Embed(
            title = f"Задача № {self.random_id}",
            description = f"{task_mem}\n\nСложность: {complexity}\n Сроки: {end_time}\n```Статус задачи: COMPLITE ?```",
            color = discord.Color.green(),
            timestamp=now
            )
        if image_mem and image_mem != "none": log_text.set_image(url=f"{image_mem}")
        log_text.set_author(name=f"{customer.display_name} ({customer.id})", icon_url=customer.display_avatar.url)
        await reestr_msg.edit(embed=log_text)
