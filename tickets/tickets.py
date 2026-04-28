import discord, os
from datetime import datetime, timezone, timedelta
from storage import storage
from tools.utils import generate_random_id
from commands.other import CloseDMView
import asyncio
from storage.storage import tickets_info, block_tickets_users, guides_storage, visas
from main import BOT
from tools.config import GUILD_ID, LOG_DEBUGS_CHANNEL, ADMIN_TICKET, CATEGORY_TICKET, OWNER_ROLE, OWNERS, LOG_TICKETS_CHANNEL, MEMBER_ROLE
pressed_users = set()
TEST_MODE = True

#--------SELECT--------

async def handle_ticket_select(interaction: discord.Interaction, value: str):
    guild = interaction.guild
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    
    if value in ("cg"):
        interaction.response.send_message("разработка", ephemeral=True)
        return

    modals = {
        "atc": AtcModal(BOT),
        "ov": OvModal(BOT),
        "co": CoModal(BOT),
        "ac": AcModal(BOT),
        "oth": OthModal(BOT)
    }

    member = guild.get_member(interaction.user.id)

    if member is None:
        try:
            member = await guild.fetch_member(interaction.user.id)
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)

            if log_channel:
                log_text = discord.Embed(
                    title="[DEBUG] Ошибка при поиске мембера",
                    description=f"`{e}`",
                    color=discord.Color.red(),
                    timestamp=now
                )

                log_text.set_author(
                    name=interaction.user.display_name,
                    icon_url=interaction.user.display_avatar.url
                )

                await log_channel.send(
                    content="<@&1348236150682419250>",
                    embed=log_text
                )

            await interaction.response.send_message(
                "Ошибка при поиске мембера.",
                ephemeral=True
            )
            return

    forbidden_roles = {
        "atc": 1342917264256532643,
        "ov": 1342917264256532643
    }

    forbidden_role_id = forbidden_roles.get(value)
    user_role_ids = {role.id for role in member.roles}

    if forbidden_role_id and forbidden_role_id in user_role_ids:
        await interaction.response.send_message(
            "Вы уже получили доступ к этой возможности — тикет не нужен.",
            ephemeral=True
        )
        return

    modal = modals.get(value)

    try:
        await interaction.response.send_modal(modal)

    except Exception as e:

        log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)

        if log_channel:
            log_text = discord.Embed(
                title="[DEBUG] Ошибка при отправке модала",
                description=f"`{e}`",
                color=discord.Color.red(),
                timestamp=now
            )

            log_text.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )

            await log_channel.send(
                content="<@&1348236150682419250>",
                embed=log_text
            )

        await interaction.response.send_message(
            "Ошибка при отправке модала.",
            ephemeral=True
        )

class GuideSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption], original_client_id: int, value: str):
        super().__init__(
            placeholder="Выберите гида из списка...",
            min_values=1,
            max_values=1,
            options=options[:25]
        )
        self.original_client_id = original_client_id
        self.ticket_value = value

    async def callback(self, interaction: discord.Interaction):
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        selected_guide_id_str = self.values[0]
        selected_guide_id = int(selected_guide_id_str)
        
        guild = interaction.guild
        client_idvalue = f"{self.original_client_id}-{self.ticket_value}"
        member = guild.get_member(self.original_client_id)
 
        try:
            data = tickets_info.get(client_idvalue)
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при поиске данных тикета",
                description = f"`{e}`\n`tickets.py:144`",
                color = discord.Color.red(),
                timestamp=now
                )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
            return

        member_to_add = guild.get_member(selected_guide_id)
        channel = guild.get_channel(data["client_channel"])
        msg = await channel.fetch_message(data["message_id"])

        if member_to_add is None or channel is None or msg is None:
            try:
                member_to_add = guild.get_member(selected_guide_id)
                channel = guild.get_channel(data["client_channel"])
                msg = await channel.fetch_message(data["message_id"])
            except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске гида, канала или сообщения",
                    description = f"`{e}`\n`tickets.py:161-163`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске гида, канала или сообщения, отчёт уже отправлен.", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            member_to_add: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True)
        }

        await channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"{member_to_add.mention} (Гид) добавлен в тикет.", ephemeral=True)
        await channel.send(f"{member_to_add.mention} вас добавили в тикет для проведения экскурса(ии).")
        await msg.edit(content=f"{member.mention} ваш гид {member_to_add.mention} скоро проведёт экскурс(ию)", view=MemberView(self.bot, client_id=self.original_client_id, value=self.ticket_value))

#--------MODALS--------

class AtcModal(discord.ui.Modal, title="Заполните колонки ниже"):
    name = discord.ui.TextInput(label="Ваше имя", placeholder="если стесняетесь, можете не говорить", required=False)
    age = discord.ui.TextInput(label="Ваш возраст", required=True, min_length=2, max_length=2)
    purpose = discord.ui.TextInput(label="Планы на город", placeholder="вы же наверняка пришли ради выполнения как-либо цели, какой именно?", required=True, min_length=1)
    reason = discord.ui.TextInput(label="В чём вы хороши?", placeholder="в актёрстве / строительстве / составлении ивентов и сценариев / работе в людьми и тд", style=discord.TextStyle.paragraph, required=True, min_length=1)
    info = discord.ui.TextInput(label="Расскажите о себе (какой вы человек и тд)", placeholder="чем больше написано, тем лучше ;)", style=discord.TextStyle.paragraph, required=True, min_length=1)

    def __init__(self): super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await process_ticket(self.bot, interaction, "atc", {
            "Имя": self.name.value or "Не указано",
            "Возраст": self.age.value,
            "Планы": self.purpose.value,
            "Умения": self.reason.value,
            "Биография": self.info.value
        })

class OvModal(discord.ui.Modal, title="Заполните колонки ниже"):
    name = discord.ui.TextInput(label="Ваше имя", placeholder="если стесняетесь, можете не говорить", required=False)
    age = discord.ui.TextInput(label="Ваш возраст", required=True, min_length=2, max_length=2)
    purpose = discord.ui.TextInput(label="Цель визита", required=True, min_length=1)
    duration = discord.ui.TextInput(label="Сколько дней планируете быть?", required=True, min_length=1)
    plans = discord.ui.TextInput(label="Чем планируете заниматься?", required=True, min_length=1)

    def __init__(self): super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await process_ticket(self.bot, interaction, "ov", {
            "Имя": self.name.value or "Не указано",
            "Возраст": self.age.value,
            "Цель визита": self.purpose.value,
            "Желаемая длительность срока": self.duration.value,
            "Планы на визу": self.plans.value
        })

class CoModal(discord.ui.Modal, title="Заполните колонки ниже"):
    subject = discord.ui.TextInput(label="Тема обращения", required=True, min_length=1)
    message = discord.ui.TextInput(label="Сообщение", style=discord.TextStyle.paragraph, required=True, min_length=1)

    def __init__(self): super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await process_ticket(self.bot, interaction, "co", {
            "Тема": self.subject.value,
            "Сообщение": self.message.value
        })

class AcModal(discord.ui.Modal, title="Заполните колонки ниже"):
    user = discord.ui.TextInput(label="На кого / на что жалоба", placeholder="если вы скажете кто именно провинился, то вы нам поможете стать лучше", required=False)
    complaint = discord.ui.TextInput(label="Опишите вашу жалобу", placeholder="Форма: 1. Суть жалобы; 2. Описание; 3. Какое вы хотите увидеть наказние?", required=True, style=discord.TextStyle.paragraph, min_length=1)

    def __init__(self): super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await process_ticket(self.bot, interaction, "ac", {
            "Виновный": self.user.value or "Не указано",
            "Обвинения": self.complaint.value
        })

class OthModal(discord.ui.Modal, title="Заполните колонки ниже"):
    question = discord.ui.TextInput(label="Ваш вопрос", required=True, style=discord.TextStyle.paragraph, min_length=1)

    def __init__(self): super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await process_ticket(self.bot, interaction, "oth", {
            "Вопрос": self.question.value
        })

class VisaDurationModal(discord.ui.Modal):
    def __init__(self, original_client_id: int, value: str):
        super().__init__(title="Установить срок действия визы")
        self.original_client_id = original_client_id
        self.value = value
        
        # Поле для ввода текста
        self.add_item(
            discord.ui.TextInput(label="Количество дней", placeholder="Введите целое число дней (например, 30)", min_length=1, max_length=2, required=True)
        )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            days_str = self.children[0].value
            days = int(days_str)

            if days == 0:
                owner_role = guild.get_role(OWNER_ROLE)
                if owner_role not in interaction.user.roles and interaction.user.id not in OWNERS:
                    await interaction.response.send_message("Только владелец может выдавать бессрочные визы.", ephemeral=True)
                    return
                client_id = self.original_client_id
                visas[client_id]["timers"].clear()
                storage.save_visas(visas)
                try:
                    data = visas.get(client_id)
                except Exception as e:
                    log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                    if log_channel:
                        log_text = discord.Embed(
                        title = "[DEBUG] Ошибка при поиске данных тикета",
                        description = f"`{e}`\n`tickets.py:754`",
                        color = discord.Color.red(),
                        timestamp=now
                        )
                        log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                        #log_text.set_footer(text=F"{formatted_time}█")
                    await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                    await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
                    return

                numberov = None
                try:
                    member = guild.get_member(self.original_client_id)
                    channel = guild.get_channel(1444455507166363798)
                    message = await channel.fetch_message(data["message_id"])
                except Exception as e:
                    log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                    if log_channel:
                        log_text = discord.Embed(
                        title = "[DEBUG] Ошибка при поиске мембера, канала или сообщения",
                        description = f"`{e}`\n`tickets.py:770-772`",
                        color = discord.Color.red(),
                        timestamp=now
                        )
                        log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                        #log_text.set_footer(text=F"{formatted_time}█")
                    await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                    await interaction.response.send_message("Ошибка при поиске мембера, канала или сообщения, отчёт уже отправлен.", ephemeral=True)
                    return
                
                numberov = storage.get_next_ticket_number("ov")

                embed = message.embeds[0]
                field_name = "Реальный срок действия визы:"
                new_value = f"**`бессрочный`**\n-# поставил срок: {interaction.user.mention} ({interaction.user.id})"     
                found = False
                for i, field in enumerate(embed.fields):
                    if field.name == field_name:
                        embed.set_field_at(i, name=field_name, value=new_value, inline=False)
                        found = True
                        break
                    
                if not found:
                    embed.add_field(name=field_name, value=new_value, inline=False)
                #embed.set_footer(text=F"{formatted_time}█")
                embed.timestamp = now
                embed.title = f"Бессрочная виза № {numberov}"
                await message.edit(content=f"# Действует\nВладелец визы: {member.mention} ({member.id})", embed=embed)
                await interaction.response.send_message(f"Срок действия визы для клиента {member.mention} обновлен на **`бессрочный`**.", ephemeral=True)
                visas[client_id]["number"] = f"{numberov}"
                storage.save_visas(visas)


                if member:
                    try:
                        channel1 = await member.create_dm()
                        message1 = await channel1.fetch_message(data["message_dm_id"])
                        embed1 = discord.Embed(
                        title="Обновление срока действия визы",
                        description=f"Ваша виза была обновлена. Новый срок действия: **бессрочный**.",
                        color=discord.Color.green(),
                        timestamp=now
                        )
                        embed1.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                        #embed1.set_footer(text=F"{formatted_time}█")
                        embed.color = discord.Color.green()
                        await message1.delete()
                        msg = await member.send(embeds=[embed, embed1])
                        msg_id = msg.id
                        visas[client_id]["message_dm_id"] = {msg_id}
                        storage.save_visas(visas)
                    except discord.Forbidden:
                        print(f"Не удалось отправить ЛС клиенту {member.id}")
                return

            if days < 0:
                await interaction.response.send_message("Количество дней должно быть положительным числом.", ephemeral=True)
                return
            
            else:
                delta = timedelta(minutes=days) if TEST_MODE else timedelta(days=days)
                expiration_date = datetime.now(msk) + delta

                # Форматируем дату для удобного хранения и чтения в JSON
                expiration_iso = expiration_date.isoformat()
                visas[client_id]["timers"].clear()
                visas[client_id]["timers"] = expiration_iso
                storage.save_visas(visas)

                client_id = f"{self.original_client_id}"
                try:
                    data = visas.get(client_id)
                except Exception as e:
                    log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                    if log_channel:
                        log_text = discord.Embed(
                        title = "[DEBUG] Ошибка при поиске данных тикета",
                        description = f"`{e}`\n`tickets.py:754`",
                        color = discord.Color.red(),
                        timestamp=now
                        )
                        log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                        #log_text.set_footer(text=F"{formatted_time}█")
                    await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                    await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
                    return

                try:
                    member = guild.get_member(self.original_client_id)
                    channel = guild.get_channel(1444455507166363798)
                    message = await channel.fetch_message(data["message_id"])
                    number = str(data["number"])
                except Exception as e:
                    log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                    if log_channel:
                        log_text = discord.Embed(
                        title = "[DEBUG] Ошибка при поиске мембера, канала или сообщения",
                        description = f"`{e}`\n`tickets.py:770-772`",
                        color = discord.Color.red(),
                        timestamp=now
                        )
                        log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                        #log_text.set_footer(text=F"{formatted_time}█")
                    await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                    await interaction.response.send_message("Ошибка при поиске мембера, канала или сообщения, отчёт уже отправлен.", ephemeral=True)
                    return

                embed = message.embeds[0]
                field_name = "Реальный срок действия визы:"
                new_value = f"до <t:{int(expiration_date.timestamp())}:F>\n-# поставил срок: {interaction.user.mention} ({interaction.user.id})"     
                found = False
                for i, field in enumerate(embed.fields):
                    if field.name == field_name:
                        embed.set_field_at(i, name=field_name, value=new_value, inline=False)
                        found = True
                        break
                    
                if not found:
                    embed.add_field(name=field_name, value=new_value, inline=False)
                #embed.set_footer(text=F"{formatted_time}█")
                embed.timestamp=now
                embed.title = f"Виза № `{number}`"
                await message.edit(content=f"# Действует\nВладелец визы: {member.mention} ({member.id})", embed=embed)
                await interaction.response.send_message(f"Срок действия визы для клиента {member.mention} обновлен на {days} дней. Истекает: <t:{int(expiration_date.timestamp())}:F>.", ephemeral=True)

                if member:
                    try:
                        channel1 = await member.create_dm()
                        message1 = await channel1.fetch_message(data["message_dm_id"])
                        embed1 = discord.Embed(
                        title="Обновление срока действия визы",
                        description=f"Ваша виза была обновлена. Новый срок действия истекает: <t:{int(expiration_date.timestamp())}:F>.",
                        color=discord.Color.yellow(),
                        timestamp=now
                        )
                        embed1.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                        embed.color = discord.Color.yellow()
                        await message1.delete()
                        msg = await member.send(embeds=[embed, embed1])
                        msg_id = msg.id
                        visas[client_id]["message_dm_id"] = {msg_id}
                        storage.save_visas(visas)
                    except discord.Forbidden:
                        print(f"Не удалось отправить ЛС клиенту {member.id}")

        except ValueError:
            await interaction.response.send_message("Пожалуйста, введите корректное целое число.", ephemeral=True)
            return

class VisaCancellationModal(discord.ui.Modal):
    def __init__(self, original_client_id: int, value: str):
        super().__init__(title="Пояснение анулирования")
        self.client_id = original_client_id
        self.value = value
        
        # Поле для ввода текста
        self.add_item(
            discord.ui.TextInput(label="Причина", min_length=1, required=False)
        )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        client_id = f"{self.client_id}"
        reason = self.children[0].value

        try:
            data = visas.get(client_id)
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске данных тикета",
                    description = f"`{e}`\n`tickets.py:1029`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
                return

        try:
            member = guild.get_member(self.client_id)
            channel = guild.get_channel(1444455507166363798)
            message = await channel.fetch_message(data["message_id"])
            temp_num = data["number_ov"]
            if temp_num is None:
                temp_num = data["number"]
            number = str(temp_num)
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при поиске мембера, канала или сообщения",
                description = f"`{e}`\n`tickets.py:770-772`",
                color = discord.Color.red(),
                timestamp=now
                )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            return
            
        embed1 = message.embeds[0]
        reason1 = reason or "Отсутствует"
        field_name = "Дата анулирования:"
        new_value = f"<t:{int(now.timestamp())}:F>\n-# анулировал: {interaction.user.mention} ({interaction.user.id})\n-# Причина: {reason1}"     
        found = False
        for i, field in enumerate(embed1.fields):
            if field.name == field_name:
                embed1.set_field_at(i, name=field_name, value=new_value, inline=False)
                found = True
                break
                    
        if not found:
            embed1.add_field(name=field_name, value=new_value, inline=False)
        #embed1.set_footer(text=F"{formatted_time}█")
        embed1.timestamp = now
        embed1.title = f"Анулированная виза № `{number}`"
        await message.edit(content=f"# Виза анулирована\nВладелец визы: {member.mention} ({self.client_id})", embed=embed1, view=None)
            
        if member:
            try:
                tourist_role = guild.get_role(1478458320841871443)
                channel1 = await member.create_dm()
                message1 = await channel1.fetch_message(data["message_dm_id"])
                embed = discord.Embed(
                title="Виза анулирована",
                    description=f"Ваша виза, выданная ранее, анулирована <t:{int(now.timestamp())}:F>.\nПричина: {reason1}",
                    color=discord.Color.red(),
                    timestamp=now
                )
                embed.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #embed.set_footer(text=F"{formatted_time}█")
                embed1.color = discord.Color.red()
                await message1.delete()
                msg = await member.send(embeds=[embed1, embed], view=CloseDMView())
                await member.remove_roles(tourist_role, reason="Анулирование визы")
                msg_id = msg.id
                visas[client_id]["message_dm_id"] = {msg_id}
                storage.save_visas(visas)
            except discord.Forbidden:
                    print(f"Не удалось отправить ЛС пользователю {self.client_id}")
        
        visas[client_id]["number"].clear()
        visas[client_id]["message_id"].clear()
        visas[client_id]["timers"] = {f"CANCELLED"}
        storage.save_ti_in(tickets_info)

#--------ASYNC--------

async def process_ticket(interaction: discord.Interaction, value1: str, form_data: dict):
    guild = interaction.guild
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    #formatted_time = now.strftime("%d.%m.%y %H:%M")
    member = interaction.user
    admin_ticket = guild.get_role(ADMIN_TICKET)

    if interaction.user.id in block_tickets_users:
        await interaction.response.send_message("Вы находитесь в чёрном списке тикет юзеров, обратитесь к администраторам за решением этой проблемы.", ephemeral=True)
        return

    client_idvalue = f"{interaction.user.id}-{value1}"
    client_id = f"{interaction.user.id}"
    if value1 not in ("ac", "oth"):
        if client_idvalue in tickets_info:
            data = tickets_info[client_idvalue]
            channel = guild.get_channel(data["client_channel"])
            if channel:
                await interaction.response.send_message(f"У вас уже есть активный тикет этого типа: {channel.mention}", ephemeral=True)
                return
    
    if value1 in ("ov"):
        if client_id in visas:
            visa = visas[client_id]
            timers = visa["timers"]
            if timers and timers in ["EXPIRED", "CANCELLED"]:
                await interaction.response.send_message(f"У вас уже была виза, её срок был истечён, прошлые данные удалены ", ephemeral=True)
                channel1 = await member.create_dm()
                message1 = await channel1.fetch_message(visa["message_dm_id"])
                await message1.delete()
                visas.pop(client_id, None)
                storage.save_visas(visas)
            elif timers:
                await interaction.response.send_message(f"У вас уже есть виза, срок вашей визы мы отправляли через бота в лс", ephemeral=True)
                return

    forbian_roles = {
            "atc": 1342917264256532643,  # Уже есть гражданство
            "ov": [1342917264256532643, 1478458320841871443]    # Уже есть гражданство и виза
        }
    if any(role.id in forbian_roles for role in interaction.user.roles):
        await interaction.response.send_message("Даннная услуга вам не нужна.", ephemeral=True)
        return
    
    if value1 in ("ov"):
        pass
    else:
        ticket_number = storage.get_next_ticket_number(value1)
        channel_name = f"🎫・{value1}-{ticket_number}"

        existing = discord.utils.get(guild.text_channels, name=channel_name)
        if existing:
            await interaction.response.send_message(f"Канал {existing.mention} уже существует.", ephemeral=True)
            return
    if value1 in ("ac"):
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False)
        }
    else:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            admin_ticket: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True),
            member: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True)
        }

    try:
        category = discord.utils.get(guild.categories, id=CATEGORY_TICKET)
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

    client_id = member.id
    random_id = generate_random_id()
    channel_ov = guild.get_channel(1444455507166363798)
    embed1 = discord.Embed(title=f"Новый тикет `{value1}` № `{random_id}`", timestamp=now)
    for key, value in form_data.items():
        embed1.add_field(name=key, value=value, inline=False)
        embed1.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        #embed1.set_footer(text=F"{formatted_time}█")

    embed2 = discord.Embed(title=f"Регистрационная виза № `{random_id}`", timestamp=now)
    for key, value in form_data.items():
        embed2.add_field(name=key, value=value, inline=False)
        embed2.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        embed2.set_footer(text=F"срочно требуется назначить срок действия█")

    embed3 = discord.Embed(title=f"Новая заявка на гражданство № `{random_id}`", timestamp=now)
    for key, value in form_data.items():
        embed3.add_field(name=key, value=value, inline=False)
        embed3.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        embed3.set_footer(text=F"не забудьте напомнить о добавлении вашего др в список чтобы вас поздравили в ваш день рождения█")
    
    view=AddAcView(client_id=client_id, value=value1)
    view1=AcceptClView(client_id=client_id, value=value1)
    view2=OvView(client_id=client_id, value=value1)
    view3=GuideView(client_id=client_id, value=value1)

    if value1 in ("ov"):
        message = await channel_ov.send(content=f"# Регистрация (действует)\nВладелец визы: {interaction.user.mention} ({client_id})\n-# <@&1342918645113946173><@&1346805415874269184>", embed=embed2, view=view2)
        message_id = message.id
        client_idvalue = f"{client_id}-{value1}"
        await interaction.response.send_message(f"Проверьте личные сообщения от бота", ephemeral=True)
        if member:
            try:
                tourist_role = guild.get_role(1478458320841871443)
                embed = discord.Embed(
                    title="Регистрация визы",
                    description=f"Вы зарегистрировали визу. В ближайшее время вы узнаете срок действия визы.",
                    color=discord.Color.green(),
                    timestamp=now
                )
                embed.set_author(name=BOT.user.display_name, icon_url=BOT.user.display_avatar.url)
                #embed.set_footer(text=F"{formatted_time}█")
                embed2.color = discord.Color.green()
                msg = await member.send(embeds=[embed2, embed])
                await member.add_roles(tourist_role, reason="Регистрация визы")
            except discord.Forbidden:
                print(f"Не удалось отправить ЛС клиенту {member.id}")
        msg_id = msg.id
        visas[client_id] = {
            "number": random_id,
            "message_id": message_id,
            "message_dm_id": msg_id
        }
        storage.save_visas(visas)
    else:
        channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites, category=category)
        client_channel=channel.id
        if value1 in ("ac"):
            message = await channel.send(content=f"<@640069373108813824> новая жалоба.", embed=embed1, view=view)
        elif value1 in ("co"):
            message = await channel.send(content=f"{member.mention} ожидайте владельца.\n-# <@640069373108813824>", embed=embed1, view=view1)
        elif value1 in ("atc"):
            message = await channel.send(content=f"{member.mention} ожидайте ответа.", embed=embed3, view=view3)
        elif value1 in ("oth"):
            message = await channel.send(content=f"{member.mention} ожидайте ответа на ваш вопрос.", embed=embed1, view=view1)
        message_id = message.id
        client_idvalue = f"{client_id}-{value1}"
        tickets_info[client_idvalue] = {
                "value": value1,
                "message_id": message_id,
                "number": ticket_number,
                "client_channel": client_channel,
                "client_id": client_id
        }
        storage.save_ti_in(tickets_info)

        view_log = discord.ui.View()
        view_log.add_item(
            discord.ui.Button(
                label="Перейти в канал",
                style=discord.ButtonStyle.link,
                url=channel.jump_url
            )
        )

        if value1 in ("ac"):
            await interaction.response.send_message(f"Ваша жалоба была отправлена, с вами свяжутся если будет необходимость", ephemeral=True)
        else:
            await interaction.response.send_message(f"Тикет создан", view=view_log, ephemeral=True)
    
        #Логирование
        log_channel = guild.get_channel(LOG_TICKETS_CHANNEL)
        if log_channel:
            log_text = discord.Embed(
            title = f"Новый тикет {channel.name}",
            description = f"## <@{client_id}> создал новый тикет типа «{value1}»\n```Действие: Создан новый тикет```\n`Тикет:` {channel.mention}\n```Статус: На ожидании```\n```Задача: Принять тикет```",
            color = discord.Color.green(),
            timestamp=now
            )
            log_text.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
            #log_text.set_footer(text=F"{formatted_time}█")
        if value1 in ("ac", "co"):
            return
        else:
            await log_channel.send(embed=log_text, view=view_log)

async def transcript_ticket(channel: discord.TextChannel, folder: str = "transcripts"):
    """Создание транскрипта тикета и возврат пути к файлу"""
    if not os.path.exists(folder):
        os.makedirs(folder)

    transcript_lines = []
    async for msg in channel.history(limit=None, oldest_first=True):
        time = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        author = msg.author.display_name
        content = msg.content if msg.content else ""
        attachments = " ".join([att.url for att in msg.attachments])

        line = f"[{time}] {author}: {content} {attachments}".strip()
        transcript_lines.append(line)

    if not transcript_lines:
        transcript_lines.append("[Пустой тикет]")

    filename = f"{folder}/{channel.name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(transcript_lines))

    return filename

#--------VIEWS--------

class AddAcView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(AddAcButton(client_id=client_id, value=value))
        self.add_item(AcceptClose(client_id=client_id, value=value))

class RemoveAcView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(RemoveAcButton(client_id=client_id, value=value))
        self.add_item(AcceptClose(client_id=client_id, value=value))

class GuideView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(AddMeButton(client_id=client_id, value=value))
        self.add_item(AddGuButton(client_id=client_id, value=value))
        self.add_item(AcceptCloseRequest(client_id=client_id, value=value))

class OvView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(OvDurButton(client_id=client_id, value=value))
        self.add_item(AcceptCancellation(client_id=client_id, value=value))

class GuideSelectView(discord.ui.View):
    def __init__(self, options: list[discord.SelectOption], client_id: int, value: str):
        super().__init__(timeout=None)
        self.add_item(GuideSelect(options, client_id, value))

class MemberView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(AddMeButton(client_id=client_id, value=value))
        self.add_item(AcceptClose(client_id=client_id, value=value))

class CloseViewRequest(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(CloseButtonRequest(client_id=client_id, value=value))

class CloseView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(CloseButton(client_id=client_id, value=value))

class DeleteView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(DeleteButton(client_id=client_id, value=value))

class AcceptClView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(AcceptClose(client_id=client_id, value=value))

class AcceptDlView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(AcceptDelete(client_id=client_id, value=value))

class CancellationView(discord.ui.View):
    def __init__(self, client_id, value):
        super().__init__(timeout=None)
        self.add_item(CancellationButton(client_id=client_id, value=value))


#--------BUTTONS--------


class AddAcButton(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Добавить отправившего", style=discord.ButtonStyle.green, custom_id=f"add_ac_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "accept_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:721-732`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1342918645113946173>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return
        owner_role = guild.get_role(OWNER_ROLE)

        if owner_role not in interaction.user.roles and interaction.user.id not in OWNERS:
            await interaction.response.send_message("Вы не имеете прав.", ephemeral=True)
            return

        client_idvalue = f"{client_id}-{value}"
        try:
            data = tickets_info.get(client_idvalue)
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске данных тикета",
                    description = f"`{e}`\n`tickets.py:754`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
                return

        try:
            member = guild.get_member(client_id)
            channel = guild.get_channel(data["client_channel"])
            message = await channel.fetch_message(data["message_id"])
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске мембера, канала или сообщения",
                    description = f"`{e}`\n`tickets.py:770-772`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске мембера, канала или сообщения, отчёт уже отправлен.", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            member: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True)
        }

        await channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"{member.mention} добавлен в тикет.", ephemeral=True)
        await channel.send(f"{member.mention} вас добавили в тикет, чтобы задать пару вопросов.")
        await message.edit(view=RemoveAcView(self.bot, client_id=client_id, value=value))

class RemoveAcButton(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Удалить из тикета", style=discord.ButtonStyle.red, custom_id=f"remove_ac_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "accept_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:806-817`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return
        
        owner_role = guild.get_role(OWNER_ROLE)
        if owner_role not in interaction.user.roles and interaction.user.id not in OWNERS:
            await interaction.response.send_message("Вы не имеете прав.", ephemeral=True)
            return

        client_idvalue = f"{client_id}-{value}"
        try:
            data = tickets_info.get(client_idvalue)
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске данных тикета",
                    description = f"`{e}`\n`tickets.py:839`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
                return

        try:
            member = guild.get_member(client_id)
            channel = guild.get_channel(data["client_channel"])
            message = await channel.fetch_message(data["message_id"])
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске мембера, канала или сообщения",
                    description = f"`{e}`\n`tickets.py:855-857`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске мембера, канала или сообщения, отчёт уже отправлен.", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False)
        }

        await channel.send(f"{member.mention} вас скоро удалят из тикета, спасибо за содействие.")
        await asyncio.sleep(5)
        await channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"{member.mention} удалён из тикета.", ephemeral=True)
        await message.edit(view=AddAcView(self.bot, client_id=client_id, value=value))

class AddMeButton(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Принять в город", style=discord.ButtonStyle.green, custom_id=f"add_mem_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "accept_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:721-732`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1342918645113946173>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return
        owner_role = guild.get_role(OWNER_ROLE)

        if owner_role not in interaction.user.roles and interaction.user.id not in OWNERS:
            await interaction.response.send_message("Вы не имеете прав.", ephemeral=True)
            return

        client_idvalue = f"{client_id}-{value}"
        try:
            data = tickets_info.get(client_idvalue)
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске данных тикета",
                    description = f"`{e}`\n`tickets.py:754`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
                return

        try:
            member = guild.get_member(client_id)
            channel = guild.get_channel(data["client_channel"])
            message = await channel.fetch_message(data["message_id"])
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске мембера, канала или сообщения",
                    description = f"`{e}`\n`tickets.py:770-772`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске мембера, канала или сообщения, отчёт уже отправлен.", ephemeral=True)
                return
        
        member_role = guild.get_role(1342917264256532643)
        await member.add_roles(member_role, reason="Принят в город")
        await interaction.response.send_message(f"{member.mention} принят в город.", ephemeral=True)
        await channel.send(f"{member.mention} поздравляем, вы приняты в город Deportant!")
        await message.edit(content=f"{member.mention} вас приняли в город!",view=AcceptClView(self.bot, client_id=client_id, value=value))

class AddGuButton(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Назначить гида", custom_id=f"trigger_guide_select:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "accept_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:1168-1179`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return
        
        owner_role = guild.get_role(OWNER_ROLE)
        if owner_role not in interaction.user.roles and interaction.user.id not in OWNERS:
            await interaction.response.send_message("Вы не имеете прав.", ephemeral=True)
            return
        
        options = []
        for guide_id in guides_storage:
            member = guild.get_member(guide_id)
            if member:
                options.append(discord.SelectOption(label=f"{member.display_name}", value=str(guide_id)))

        if not options:
            await interaction.response.send_message("Нет активных гидов на сервере.", ephemeral=True)
            return
        
        await interaction.response.send_message("Пожалуйста, выберите гида, которого нужно добавить в тикет:", view=GuideSelectView(self.bot, options=options[:25], client_id=client_id, value=value), ephemeral=True)

class OvDurButton(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Назначить срок визы", style=discord.ButtonStyle.green, custom_id=f"ov_dur_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "accept_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:721-732`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1342918645113946173>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return
        
        owner_role = guild.get_role(OWNER_ROLE)
        admin_ticket = guild.get_role(ADMIN_TICKET)
        if owner_role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
            await interaction.response.send_message("Вы не имеете прав.", ephemeral=True)
            return

        modal = VisaDurationModal(self.bot,original_client_id=client_id, value=value)
        await interaction.response.send_modal(modal)

class CloseButtonRequest(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Подтвердить", style=discord.ButtonStyle.danger, custom_id=f"close_button_request:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "accept_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:892-903`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=f"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return

        # ⛔ Проверка: уже нажимал?
        user_key = f"{interaction.user.id}:{self.custom_id}"
        if user_key in pressed_users:
            await interaction.response.send_message("Вы уже отправили запрос на закрытие.", ephemeral=True)
            return
        pressed_users.add(user_key)

        if interaction.user.id != client_id:
            await interaction.response.send_message("Только владелец тикета может сделать запрос.", ephemeral=True)
            return
        
        client_idvalue = f"{client_id}-{value}"

        try:
            data = tickets_info.get(client_idvalue)
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске данных тикета",
                    description = f"`{e}`\n`tickets.py:932`",
                    color = discord.Color.red(),
                    timestamp= now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
                return

        try:
            member = guild.get_member(client_id)
            channel = guild.get_channel(data["client_channel"])
            message = await channel.fetch_message(data["message_id"])
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске мембера, канала или сообщения",
                    description = f"`{e}`\n`tickets.py:948-950`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске мембера, канала или сообщения, отчёт уже отправлен.", ephemeral=True)
                return

        admin_ticket = guild.get_role(ADMIN_TICKET)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True),
            admin_ticket: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True)
        }
        await channel.edit(overwrites=overwrites)
        await channel.send(f"{admin_ticket.mention} <@{client_id}> желает закрыть тикет")
        await message.edit(content=f"<@{client_id}> скоро с вами свяжуться чтобы закрыть тикет.", view=AcceptClView(self.bot, client_id=client_id, value=value))

        #Логирование
        log_channel = guild.get_channel(LOG_TICKETS_CHANNEL)
        if log_channel:
            log_text = discord.Embed(
            title = f"Запрос на закрытие тикета",
            description = f"## <@{interaction.user.id}> хочет закрыть свой тикет типа «{value}»\n```Действие: Запрос принят и отправлен администроторам тикетов```\n`Тикет:` {channel.mention}\n```Статус: На расмотрении```\n```Задача: Узнать причину```",
            color = discord.Color.yellow()
        )
        await log_channel.send(embed=log_text)
             
class CloseButton(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Подтвердить", style=discord.ButtonStyle.danger, custom_id=f"close_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "close_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:994-1005`",
                color = discord.Color.red(),
                timestamp=now
                )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=f"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return

        client_idvalue = f"{client_id}-{value}"
        owner_role = guild.get_role(OWNER_ROLE)
        admin_ticket = guild.get_role(ADMIN_TICKET)

        if owner_role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
            await interaction.response.send_message("Вы не можете закрыть этот тикет.", ephemeral=True)
            return

        try:
            data = tickets_info.get(client_idvalue)
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске данных тикета",
                    description = f"`{e}`\n`tickets.py:1029`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске данных тикета, отчёт уже отправлен.", ephemeral=True)
                return

        try:
            channel = guild.get_channel(data["client_channel"])
            ticket_number = int(data["number"])
            message = await channel.fetch_message(data["message_id"])
        except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске канала, номера или сообщения",
                    description = f"`{e}`\n`tickets.py:1045-1047`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске канала, номера или сообщения, отчёт уже отправлен.", ephemeral=True)
                return

        guild = interaction.guild
        # Удаляем из хранилища
        tickets_info.pop(client_idvalue, None)
        storage.save_ti_in(tickets_info)

        user_key = f"{interaction.user.id}:{self.custom_id}"
        pressed_users.discard(user_key)

        # Закрываем канал для всех
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False)
        }
        channel_name = f"✅・{value}-{ticket_number}"
        category = guild.get_channel(1376938513609654292)
        await interaction.response.send_message("Тикет закрыт.", ephemeral=True)
        await channel.send(f"<@&1342918645113946173> <@{interaction.user.id}> закрыл тикет.")
        await message.edit(view=None)
        await asyncio.sleep(5)
        await channel.edit(name=channel_name, overwrites=overwrites, category=category)
        await message.edit(view=AcceptDlView(self.bot, client_id=client_id, value=value))

        #Логирование
        log_channel = guild.get_channel(LOG_TICKETS_CHANNEL)
        view_log = discord.ui.View()
        view_log.add_item(
            discord.ui.Button(
                label="Перейти в канал",
                style=discord.ButtonStyle.link,
                url=channel.jump_url
            )
        )
        if log_channel:
            log_text = discord.Embed(
            title = f"Архивация тикета",
            description = f"## <@{interaction.user.id}> закрыл тикет <@{client_id}> типа «{value}»\n```Действие: Админ решил тикет```\n`Тикет:` {channel.mention}\n```Статус: Закрыт | Решён```\n```Задача: сделать транскрипцию```",
            color = discord.Color.yellow()
        )
        if value in ("ac", "co"):
            return
        else:
            await log_channel.send(embed=log_text, view=view_log)

class DeleteButton(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Подтвердить", style=discord.ButtonStyle.danger, custom_id=f"delete_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "decline_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:1104-1115`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return

        owner_role = guild.get_role(OWNER_ROLE)
        admin_ticket = guild.get_role(ADMIN_TICKET)

        if owner_role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
            await interaction.response.send_message("Вы не имеете прав.", ephemeral=True)
            return
        
        transcript_file = await transcript_ticket(interaction.channel)

        await interaction.response.send_message("<@&1342918645113946173> Канал будет удалён через 15 секунд...")
        await asyncio.sleep(15)

        #Логирование
        log_channel = guild.get_channel(LOG_TICKETS_CHANNEL)
        if log_channel:
            log_text = discord.Embed(
            title = f"Удаление тикета",
            description = f"## <@{interaction.user.id}> удалил тикет <@{client_id}> типа «{value}»\n```Действие: Админ тикетов удалил тикет```\n`Тикет:` `отсутствует`\n```Статус: Удалён```\n```Задача: отсутствует```",
            color = discord.Color.red()
        )
        if value in ("ac", "co"):
            await log_channel.send(file=discord.File(transcript_file))
        else:
            await log_channel.send(embed=log_text, file=discord.File(transcript_file))

        if os.path.exists(transcript_file):
            os.remove(transcript_file)

        await interaction.channel.delete()

class CancellationButton(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Подтвердить", style=discord.ButtonStyle.danger, custom_id=f"cancellation_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "close_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:994-1005`",
                color = discord.Color.red(),
                timestamp=now
                )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=f"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return

        owner_role = guild.get_role(OWNER_ROLE)
        admin_ticket = guild.get_role(ADMIN_TICKET)
        if owner_role not in interaction.user.roles and admin_ticket not in interaction.user.roles and interaction.user.id not in OWNERS:
            await interaction.response.send_message("Вы не можете обнулять визы.", ephemeral=True)
            return
        
        modal = VisaCancellationModal(self.bot,original_client_id=client_id, value=value)
        await interaction.response.send_modal(modal)

#--------ACCEPT--------

class AcceptCancellation(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Анулировать визу", style=discord.ButtonStyle.danger, custom_id=f"ov_cancellation_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "decline_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:1275-1286`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return

        await interaction.response.send_message("Вы уверены что хотите закрыть тикет? Открыть его будет невозможно!", view=CancellationView(self.bot, client_id=client_id, value=value), ephemeral=True)

class AcceptCloseRequest(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Запросить закрытие", style=discord.ButtonStyle.danger, custom_id=f"ac_close_request_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        now = datetime.now(timezone(timedelta(hours=3)))
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "decline_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:1238-1249`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return

        await interaction.response.send_message("Вы уверены что хотите запросить закрытие тикета? Открыть его будет невозможно!", view=CloseViewRequest(self.bot, client_id=client_id, value=value), ephemeral=True)

class AcceptClose(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Закрыть", style=discord.ButtonStyle.danger, custom_id=f"ac_close_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        now = datetime.now(timezone(timedelta(hours=3)))
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "decline_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:1275-1286`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return

        await interaction.response.send_message("Вы уверены что хотите закрыть тикет? Открыть его будет невозможно!", view=CloseView(self.bot, client_id=client_id, value=value), ephemeral=True)

class AcceptDelete(discord.ui.Button):
    def __init__(self, client_id: int, value: str): super().__init__(label="Удалить", style=discord.ButtonStyle.danger, custom_id=f"ac_delete_button:{client_id};{value}")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        now = datetime.now(timezone(timedelta(hours=3)))
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        try:
            # Формат custom_id: "decline_client_button:123456789;value"
            parts = self.custom_id.split(":")
            if len(parts) != 2:
                raise ValueError(f"Неверный формат custom_id: {self.custom_id}")
                
            client_id_with_value = parts[1]  # "123456789;value"
            id_value_parts = client_id_with_value.split(";")  # ["123456789", "value"]
            
            if len(id_value_parts) != 2:
                raise ValueError(f"Неверный формат client_id_with_value: {client_id_with_value}")
                
            client_id = int(id_value_parts[0])
            value = id_value_parts[1]
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при разборе custom_id",
                description = f"`{e}`, `custom_id = {self.custom_id}`\n`tickets.py:1312-1323`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка в идентификаторе клиента, отчёт уже отправлен.", ephemeral=True)
            return

        await interaction.response.send_message("Вы уверены что хотите удалить тикет? Восстановить его будет невозможно!", view=DeleteView(self.bot, client_id=client_id, value=value), ephemeral=True)



# НЕ АКТУАЛЬНО
class MySelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild):
        emoji_atc = discord.utils.get(guild.emojis, id = 1376868982656860201)
        emoji_ov = discord.utils.get(guild.emojis, id = 1376925740469194802)
        emoji_co = discord.utils.get(guild.emojis, id = 1376870073758912612)
        emoji_ac = discord.utils.get(guild.emojis, id = 1376924045764726919)
        emoji_oth = discord.utils.get(guild.emojis, id = 1376871295676973189)

        options = [
            discord.SelectOption(label="Подать заявку в город", description="Стань жителем нашего дружного города!", value="atc", emoji=emoji_atc),
            discord.SelectOption(label="Получить визу", description="Получи визу на посещение города!", value="ov", emoji=emoji_ov),
            discord.SelectOption(label="Связь с владельцем", description="Хочешь предложить владельцу сделку и тд?", value="co", emoji=emoji_co),
            discord.SelectOption(label="Анонимная жалоба", description="Всё очень анонимно!", value="ac", emoji=emoji_ac),
            discord.SelectOption(label="Другое", description="Остались вопросы?", value="oth", emoji=emoji_oth)
        ]
        super().__init__(placeholder="Выберите нужную вам услугу", disabled=True,  min_values=1, max_values=1, options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        now = datetime.now(timezone(timedelta(hours=3)))
        #formatted_time = now.strftime("%d.%m.%y %H:%M")
        value = self.values[0]
        modals = {
            "atc": AtcModal(BOT),
            "ov": OvModal(BOT),
            "co": CoModal(BOT),
            "ac": AcModal(BOT),
            "oth": OthModal(BOT)
        }
        member = interaction.guild.get_member(interaction.user.id)
        if member is None:
            try:
                member = await interaction.guild.fetch_member(interaction.user.id)
            except Exception as e:
                log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
                if log_channel:
                    log_text = discord.Embed(
                    title = "[DEBUG] Ошибка при поиске мембера",
                    description = f"`{e}`\n`tickets.py:52`",
                    color = discord.Color.red(),
                    timestamp=now
                    )
                    log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                await interaction.response.send_message("Ошибка при поиске мембера, отчёт уже отправлен.", ephemeral=True)
            return

        forbidden_roles = {
            "atc": MEMBER_ROLE,  # Уже есть гражданство
            "ov": MEMBER_ROLE    # Уже есть гражданство
        }

        forbidden_role_id = forbidden_roles.get(value)
        user_role_ids = {role.id for role in member.roles}

        if forbidden_role_id and forbidden_role_id in user_role_ids:
            await interaction.response.send_message("Вы уже получили доступ к этой возможности — тикет не нужен.", ephemeral=True)
            return
        
        modal = modals.get(value)
        try:
            await interaction.response.send_modal(modal)
        except Exception as e:
            log_channel = guild.get_channel(LOG_DEBUGS_CHANNEL)
            if log_channel:
                log_text = discord.Embed(
                title = "[DEBUG] Ошибка при отправке модала",
                description = f"`{e}`\n`tickets.py:82`",
                color = discord.Color.red(),
                timestamp=now
             )
                log_text.set_author(name={interaction.user.display_name}, icon_url=interaction.user.display_avatar.url)
                #log_text.set_footer(text=F"{formatted_time}█")
            await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
            await interaction.response.send_message("Ошибка при отправке модала, отчёт уже отправлен.", ephemeral=True)
            return
