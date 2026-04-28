import discord, asyncio, aiohttp
from datetime import datetime, timezone, timedelta
from discord import AuditLogAction
from storage.storage import blocked_dm_users, save_invites, load_invites
from tools.start import build_activity_embed, build_roles_embed, build_roles_embed2, build_activity_embed2
from tools.config import ROLES_TO_TRACK, ROLES_TO_TRACK_2, GUILD_ID, LOG_SERVER_CHANNEL, LOG_MESSAGE_CHANNEL
from tools.utils import format_message_content
from collections import Counter
from commands.session import read_from_text, BlockPos
from main import BOT


#@bot.event
#async def on_member_leave(member: discord.Member):
activity_update_task = None
activity_update_lock = asyncio.Lock()
activity_update_task2 = None
activity_update_lock2 = asyncio.Lock()

async def schedule_activity_update(delay):
    guild = BOT.get_guild(GUILD_ID)
    global activity_update_task

    async with activity_update_lock:
        if activity_update_task and not activity_update_task.done():
            return  # уже запланировано

        async def delayed():
            await asyncio.sleep(delay)
            await build_activity_embed(guild)

        activity_update_task = asyncio.create_task(delayed())

async def schedule_activity_update2(delay):
    guild = BOT.get_guild(GUILD_ID)
    global activity_update_task2

    async with activity_update_lock2:
        if activity_update_task2 and not activity_update_task2.done():
            return  # уже запланировано

        async def delayed():
            await asyncio.sleep(delay)
            await build_activity_embed2(guild)

        activity_update_task2 = asyncio.create_task(delayed())

def setup_logs():

    @BOT.event
    async def on_member_join(member: discord.Member):
        guild = member.guild
        role = guild.get_role(1362927647268667463)
        guest_role = guild.get_role(1341854326607577178)

        await member.add_roles(guest_role, reason="Новый участник")
        await member.add_roles(role, reason="Новый участник")

        current_invites = await guild.invites()
        stored_invites = load_invites()

        for invite in current_invites:
            for user_id, data in stored_invites.items():
                if data["invite"] == invite.code:
                    if invite.uses > data["uses"]:
                        data["uses"] = invite.uses
                        save_invites(stored_invites)

                    ref_user = guild.get_member(user_id)
                    if not ref_user:
                        try:
                            ref_user = await guild.fetch_member(user_id)
                        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                            await invite.delete(reason="Владелец покинул сервер")
                            stored_invites.pop(str(user_id))
                            save_invites(stored_invites)
                            return
                    msk = timezone(timedelta(hours=3))
                    now = datetime.now(msk)
                    log_channel = guild.get_channel(LOG_SERVER_CHANNEL)

                    if log_channel and ref_user:
                        log_text = discord.Embed(
                            title="Новый пользователь",
                            description=(
                                f"{member.mention} зашёл по реферальной ссылке "
                                f"{ref_user.mention} "
                                f"(<https://discord.gg/{invite.code}>)\n"
                                f"* Всего использований: **{invite.uses}**"
                            ),
                            timestamp=now
                        )
                        log_text.set_footer(text=f"{member.id}")
                        log_text.set_author(
                            name=f"{ref_user.display_name} ({ref_user.id})",
                            icon_url=ref_user.display_avatar.url
                        )
                        await log_channel.send(embed=log_text)

                    if ref_user:
                        try:
                            await ref_user.send(
                                f"🎉 По вашей реферальной ссылке зашёл **{member.mention}**!\n"
                                f"🔗 Ссылка: https://discord.gg/{invite.code}\n"
                                f"📊 Всего использований: **{invite.uses}**"
                            )
                        except (discord.Forbidden, discord.HTTPException):
                            pass


    @BOT.event
    async def on_member_remove(member: discord.Member):
        guild = member.guild
        log_channel = guild.get_channel(LOG_SERVER_CHANNEL)
        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        current_invites = await guild.invites()

        if log_channel:
            embed = discord.Embed(
                title="Пользователь покинул сервер",
                description=f"{member.mention} покинул сервер.",
                timestamp=now
            )
            embed.set_footer(text=f"{member.id}")
            embed.set_author(
                name=f"{member.display_name}",
                icon_url=member.display_avatar.url
            )
            await log_channel.send(embed=embed)

        stored_invites = load_invites()
        for invite in current_invites:
            for user_id, data in stored_invites.items():
                if data["invite"] == invite.code:
                    if int(user_id) == member.id:
                        try:
                            await invite.delete(reason="Владелец покинул сервер")
                            stored_invites.pop(str(user_id))
                            save_invites(stored_invites)
                        except Exception:
                            pass


    @BOT.event
    async def on_message(message: discord.Message):
        guild = BOT.get_guild(GUILD_ID)
        if message.author.bot:
            return

        if message.author.id in blocked_dm_users:
            if isinstance(message.channel, discord.DMChannel):
                return

        if isinstance(message.channel, discord.DMChannel):

            log_channel = guild.get_channel(LOG_MESSAGE_CHANNEL)
            if log_channel:
                embed = discord.Embed(
                    title="Новое сообщение боту",
                    description=(
                        f"{message.author.mention} написал новое сообщение боту в лс:\n"
                        f"```{message.content or '❌ Ошибка ❌'}```"
                    ),
                    color=discord.Color.blue()
                )
                embed.set_author(
                    name=message.author.display_name,
                    icon_url=message.author.display_avatar.url
                )
                embed.timestamp = message.created_at

                await log_channel.send(embed=embed)

                for attachment in message.attachments:
                    await log_channel.send(file=await attachment.to_file())
        else:
            await log_message_event("create", message)
            for attachment in message.attachments:
                if message.channel.id != 1374117081720688711:
                    continue
                if not attachment.filename.endswith(".bs"):
                    continue

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(str(attachment.url)) as resp:
                            if resp.status != 200:
                                await message.reply(content=f"Ошибка скачивания файла.", mention_author=False, allowed_mentions=discord.AllowedMentions.none())
                                return
                        text = await resp.text()

                    placed = 0
                    removed = 0
                    nulls = 0
                    block_map = {}

                    async for row in read_from_text(text):
                        pos = BlockPos(row.x, row.y, row.z, row.dim)

                        if row.block is None:
                            nulls += 1
                            continue

                        if row.action == 1:
                            placed += 1
                            block_map[pos] = row.block
                        elif row.action == 2:
                            removed += 1
                            block_map.pop(pos, None)

                    result = Counter(block_map.values())
                    sorted_result = dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
                    dim_counter = Counter(pos.dim for pos in block_map.keys())

                    response_text = (
                        f"Всего установлено: {placed}\n"
                        f"Всего сломано: {removed}\n\n"
                        "Поставленные блоки (топ 50):\n"
                    )

                    for block, count in list(sorted_result.items()):
                        clean_name = str(block).replace("minecraft:", "")[:50]
                        response_text += f"{clean_name} — {count}\n"
        
                    dimension_names = {1: "Обычный мир", 2: "Ад", 3: "Энд"}
                    response_text += "\nИзмерения:\n"
                    for dim, count in dim_counter.items():
                        name = dimension_names.get(dim, f"Неизвестное измерение ({dim})")
                        response_text += f"{name} — {count}\n"

                    await message.reply(content=f"```{response_text}```", mention_author=False, allowed_mentions=discord.AllowedMentions.none())

                except Exception as e:
                    await message.reply(content=f"Ошибка обработки файла: {e}", mention_author=False, allowed_mentions=discord.AllowedMentions.none())
        await BOT.process_commands(message)

    @BOT.event
    async def on_message_delete(message: discord.Message):
        if message.author.bot:
            return
        await log_message_event("delete", message)


    @BOT.event
    async def on_message_edit(before: discord.Message, after: discord.Message):
        if after.author.bot:
            return
        await log_message_event("edit", after, before)


    async def log_message_event(event_type: str, message: discord.Message, before: discord.Message = None):
        guild = BOT.get_guild(GUILD_ID)
        log_channel = guild.get_channel(LOG_MESSAGE_CHANNEL)
        if not log_channel:
            return

        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)
        EDIT = False
        EDIT2 = False

        embed = discord.Embed(timestamp=now)
        embed.set_footer(text=f"ID сообщения: {message.id}")
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )

        view_log = discord.ui.View()
        view_log.add_item(
            discord.ui.Button(
                label="Перейти к сообщению",
                style=discord.ButtonStyle.link,
                url=message.jump_url
            )
        )

        content = format_message_content(message)
        deleter = f"<@{message.author.id}>"

        await asyncio.sleep(1)

        try:
            async for entry in message.guild.audit_logs(
                limit=5,
                action=AuditLogAction.message_delete
            ):
                if (
                    entry.target.id == message.author.id
                    and entry.extra.channel.id == message.channel.id
                    and entry.extra.count >= 1
                ):
                    deleter = f"<@{entry.user.id}>"
                    break
        except Exception:
            pass

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        if event_type == "create":
            embed.title = "Новое сообщение"
            embed.description = (
                f"<@{message.author.id}> написал в <#{message.channel.id}>:\n"
                f"```{content}```"
            )
            embed.color = discord.Color.green()
            EDIT = True
            if message.channel.id == 1442605503892160662:
                EDIT2 = True

        elif event_type == "delete":
            embed.title = "Сообщение удалено"
            embed.description = (
                f"{deleter} удалил сообщение в <#{message.channel.id}>:\n"
                f"```{content}```"
            )
            embed.color = discord.Color.red()
            EDIT = True
            if message.channel.id == 1442605503892160662:
                EDIT2 = True

        elif event_type == "edit" and before:
            if (
                before.content == message.content
                and not message.attachments
                and not message.stickers
                and not message.embeds
            ):
                return

            embed.title = "Сообщение отредактировано"
            embed.description = (
                f"<@{before.author.id}> отредактировал сообщение "
                f"в <#{before.channel.id}>"
            )

            before_content = format_message_content(before)
            after_content = format_message_content(message)

            embed.add_field(
                name="До",
                value=f"```{before_content}```",
                inline=False
            )
            embed.add_field(
                name="После",
                value=f"```{after_content}```",
                inline=False
            )
            embed.color = discord.Color.orange()
        
        if EDIT:
            await schedule_activity_update(guild, delay=30)
        if EDIT2:
            await schedule_activity_update2(guild, delay=30)
        await log_channel.send(embed=embed, view=view_log)


    @BOT.event
    async def on_member_update(before: discord.Member, after: discord.Member):
        before_roles = set(before.roles)
        after_roles = set(after.roles)

        added_roles = after_roles - before_roles
        removed_roles = before_roles - after_roles

        if not added_roles and not removed_roles and before.display_name == after.display_name and before.avatar == after.avatar:
            return

        guild = BOT.get_guild(GUILD_ID)
        log_channel = guild.get_channel(LOG_SERVER_CHANNEL)
        if not log_channel:
            return

        msk = timezone(timedelta(hours=3))
        now = datetime.now(msk)

        description = ""
        executor = None
        color = 0xFFFFFF
        EDIT = False
        EDIT_2 = False

        changed_role_ids = {role.id for role in added_roles | removed_roles}

        # РОЛИ
        if added_roles or removed_roles:
            async for entry in guild.audit_logs(limit=5, action=AuditLogAction.member_role_update):
                if entry.target.id == after.id:
                    executor = entry.user
                    break

            if added_roles:
                description += f"➕ Добавлены роли: {', '.join(r.name for r in added_roles)}\n"
            if removed_roles:
                description += f"➖ Удалены роли: {', '.join(r.name for r in removed_roles)}\n"

            if executor:
                description += f"**Изменил роли:** {executor.mention}\n"

            color = 0x00FF00 if added_roles else 0xFF0000

            for item in ROLES_TO_TRACK:
                roles = item.get("roles")
                if not roles:
                    continue

                tracked_role_ids = roles if isinstance(roles, list) else [roles]

                if any(rid in changed_role_ids for rid in tracked_role_ids):
                    EDIT = True
            
            for item in ROLES_TO_TRACK_2:
                roles = item.get("roles")
                if not roles:
                    continue

                tracked_role_ids = roles if isinstance(roles, list) else [roles]

                if any(rid in changed_role_ids for rid in tracked_role_ids):
                    EDIT_2 = True

        # НИК
        if before.display_name != after.display_name:
            async for entry in guild.audit_logs(limit=5, action=AuditLogAction.member_update):
                if entry.target.id == after.id:
                    executor = entry.user
                    break

            description += f"✏️ Изменён ник: **{before.display_name} → {after.display_name}**\n"
            if executor:
                description += f"**Изменил ник:** {executor.mention}\n"

            color = 0xFFFF00

        # АВАТАР
        if before.avatar != after.avatar:
            async for entry in guild.audit_logs(limit=5, action=AuditLogAction.member_update):
                if entry.target.id == after.id:
                    executor = entry.user
                    break

            description += "🖼 Изменён аватар\n"
            if executor:
                description += f"**Изменил аватар:** {executor.mention}\n"

            color = 0x00FFFF

        if not description:
            return

        embed = discord.Embed(
            title=f"Обновление участника: {after}",
            description=description,
            color=color,
            timestamp=now
        )

        embed.set_author(name=str(after), icon_url=after.display_avatar.url)
        embed.set_footer(text=f"ID пользователя: {after.id}")

        await log_channel.send(embed=embed)

        if EDIT:
            await build_roles_embed(guild)
        if EDIT_2:
            await build_roles_embed2(guild)
