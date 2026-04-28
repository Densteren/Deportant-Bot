import discord, random
from datetime import datetime, timezone, timedelta, timezone as dt_timezone
from storage.storage import load_visas, save_visas, load_bd_users
from discord.ext import tasks
from config import ROLES_TO_TRACK, ROLES_TO_TRACK_2, BULLETIN_BOARD, GUILD_ID, BOT_ID, LOG_DEBUGS_CHANNEL, TOURIST_ROLE
from tools.utils import get_channel_popularity, get_most_active_members_by_messages, get_most_active_members_by_reports, parse_timezone, format_age, get_members
from commands.other import CloseDMView
from main import BOT

@tasks.loop(seconds=10)
async def change_status():
        guild = BOT.get_guild(GUILD_ID)
        if not guild: return
        members = [member for member in guild.members if not member.bot and member.status != discord.Status.offline]
        if not members: return
        activity = random.choice([
            discord.Activity(type=discord.ActivityType.watching, name=f"за чатами сервера {guild.name}"),
            discord.Activity(type=discord.ActivityType.watching, name=f"на {random.choice(members).display_name}"),
            discord.Activity(type=discord.ActivityType.watching, name="правила"),
            discord.Activity(type=discord.ActivityType.watching, name=f"на {random.choice(members).display_name}"),
            discord.Activity(type=discord.ActivityType.listening, name="ваши предложения"),
            discord.Activity(type=discord.ActivityType.watching, name=f"на {random.choice(members).display_name}"),
            discord.Activity(type=discord.ActivityType.listening, name="наставления администрации"),
            discord.Activity(type=discord.ActivityType.watching, name=f"на {random.choice(members).display_name}"),
            discord.Activity(type=discord.ActivityType.playing, name="Minecraft"),
            discord.Activity(type=discord.ActivityType.watching, name=f"на {random.choice(members).display_name}")
        ])
        await BOT.change_presence(status=discord.Status.dnd, activity=activity)

@tasks.loop(hours=1)
async def birthday_checker():
    guild = BOT.get_guild(GUILD_ID)
    for user_id, data in load_bd_users().items():
        local_time = datetime.now(dt_timezone.utc).astimezone(parse_timezone(data["timezone"]))
        if (local_time.hour == 0 and local_time.minute == 0 and local_time.day == data["day"] and local_time.month == data["month"]):
            user = guild.get_member(int(user_id))
            if not user: continue
            channel = guild.get_channel(BULLETIN_BOARD)
            if not channel: continue
            if data["year"]:
                await channel.send(f"🎉 С ДНЁМ РОЖДЕНИЯ {user.mention}!!! 🎂\nСегодня имениннику исполнилось {format_age(local_time.year - data["year"])}\n-# местное время: {local_time.strftime("%d.%m %H:%M")} ({parse_timezone(data["timezone"])})\n-# ||<@&1342917264256532643>||")
                try: await user.send(f"🎉 С ДНЁМ РОЖДЕНИЯ!!! 🎂\nСегодня вам исполнилось {format_age(local_time.year - data["year"])}\n-# местное время: {local_time.strftime("%d.%m %H:%M")} ({parse_timezone(data["timezone"])})", view=CloseDMView())
                except: pass
            else:
                await channel.send(f"🎉 С ДНЁМ РОЖДЕНИЯ {user.mention}!!! 🎂\n-# местное время: {local_time.strftime("%d.%m %H:%M")} ({parse_timezone(data["timezone"])})\n-# ||<@&1342917264256532643>||")
                try: await user.send(f"🎉 С ДНЁМ РОЖДЕНИЯ!!! 🎂\n-# местное время: {local_time.strftime("%d.%m %H:%M")} ({parse_timezone(data["timezone"])})", view=CloseDMView())
                except: pass

@tasks.loop(minutes=1)
async def check_visa_expirations():
    guild = BOT.get_guild(GUILD_ID)
    visas = load_visas()
    expired_client_ids = []
    user = guild.get_member(BOT_ID)
    if not guild: return
    now = datetime.now(timezone(timedelta(hours=3)))
        
    for client_id_str, data in visas.items():
        try: expiration_date = datetime.fromisoformat(data["timers"])
        except Exception: continue
        if now >= expiration_date: expired_client_ids.append(client_id_str)
        try:
            member = guild.get_member(int(client_id_str))
            channel = guild.get_channel(1444455507166363798)
            message = await channel.fetch_message(data["message_id"])
            temp_num = data["number_ov"]
            if temp_num is None: temp_num = data["number"]
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
                    log_text.set_author(name={user.display_name}, icon_url=user.display_avatar.url)
                    #log_text.set_footer(text=F"{formatted_time}█")
                await log_channel.send(content="<@&1348236150682419250>", embed=log_text)
                return
            
        embed1 = message.embeds[0]
        field_name = "Дата анулирования:"
        new_value = f"<t:{int(now.timestamp())}:F>\n-# анулировал: {user.mention} ({user.id})\n-# Причина: истёк срок"     
        found = False
        for i, field in enumerate(embed1.fields):
            if field.name == field_name:
                embed1.set_field_at(i, name=field_name, value=new_value, inline=False)
                found = True
                break
                    
        if not found: embed1.add_field(name=field_name, value=new_value, inline=False)
        #embed1.set_footer(text=F"{formatted_time}█")
        embed1.timestamp = now
        embed1.title = f"Истёкшая виза № `{number}`"
        await message.edit(content=f"# Виза истекла\nВладелец визы: {member.mention} ({int(client_id_str)})", embed=embed1, view=None)
            
        if member:
            try:
                channel1 = await member.create_dm()
                message1 = await channel1.fetch_message(data["message_dm_id"])
                embed = discord.Embed(
                    title="Виза истекла",
                        description=f"Ваша виза, выданная ранее, анулирована <t:{int(now.timestamp())}:F>.\nПричина: истёк срок",
                        color=discord.Color.red(),
                        timestamp=now)
                embed.set_author(name={user.display_name}, icon_url=user.display_avatar.url)
                #embed.set_footer(text=F"{formatted_time}█")
                embed1.color = discord.Color.red()
                await message1.delete()
                msg = await member.send(embeds=[embed1, embed], view=CloseDMView())
                await member.remove_roles(guild.get_role(TOURIST_ROLE), reason="Анулирование визы")
                msg_id = msg.id
                visas[client_id_str]["message_dm_id"] = {msg_id}
            except discord.Forbidden: print(f"Не удалось отправить ЛС пользователю {int(client_id_str)}")

    # удаляем истёкшие
    for client_id_str in expired_client_ids: visas[client_id_str]["number"].clear(), visas[client_id_str]["message_id"].clear(), visas[client_id_str]["timers"] = "EXPIRED"
    if expired_client_ids: save_visas(visas)

async def build_roles_embed():
    guild = BOT.get_guild(GUILD_ID)
    now = datetime.now(timezone(timedelta(hours=3)))
    lines = []
    for item in ROLES_TO_TRACK:
        t = item["type"]

        if t == "h2":
            members = await get_members(guild, item["roles"])
            role = guild.get_role(item["roles"])
            lines.append(f'## {item["emoji"]} **{item["title"]}:** {members}')
            #lines.append(f'## **{role.mention}:** {members}')
            continue

        if t == "h3":
            members = await get_members(guild, item["roles"])
            role = guild.get_role(item["roles"])
            lines.append(f'\n### {item["emoji"]} **{item["title"]}:** {members}')
            #lines.append(f'\n### **{role.mention}:** {members}')
            continue

        if t == "h3_n":
            role = guild.get_role(item["roles"])
            lines.append(f'\n### {item["emoji"]} **{item["title"]}:**')
            #lines.append(f'\n### **{role.mention}:**')
            continue

        if t == "block":
            members = await get_members(guild, item["roles"])
            role = guild.get_role(item["roles"])
            lines.append(f'> - {item["emoji"]} {item["title"]}: {members}')
            #lines.append(f'> - {role.mention}: {members}')
            continue
        
        if t == "block_ih":
            members = await get_members(guild, item["roles"])
            role = guild.get_role(item["roles"])
            lines.append(f'> - {item["emoji"]} {item["title"]}: {members} (ВРИО)')
            #lines.append(f'> - {role.mention}: {members}')
            continue

        if t == "n|":
            lines.append('\n')
            continue

        if t == "line":
            members = await get_members(guild, item["roles"])
            role = guild.get_role(item["roles"])
            lines.append(f'{item["emoji"]} **{item["title"]}:** {members}\n')
            #lines.append(f'**{role.mention}:** {members}\n')
            continue


    roles_embed = discord.Embed(
    title="Роли",
    description=f"\n".join(lines),
    timestamp=now
    )
    roles_embed.set_footer(text="Последнее обновление")
    
    global status_channel_id, status_message_id
    channel = guild.get_channel(status_channel_id)
    try: msg = await channel.fetch_message(status_message_id)
    except discord.NotFound: return
    old_embeds = msg.embeds
    activity_embed = old_embeds[1]
    await msg.edit(embeds=[roles_embed, activity_embed])

async def build_activity_embed():
    guild = BOT.get_guild(GUILD_ID)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    if not guild: return

    most_active_msg = await get_most_active_members_by_messages(guild)
    most_popular, least_popular = await get_channel_popularity(guild)
    #most_active_voice, voice_minutes = get_most_active_in_voice(guild)
    icons = ["🥇", "🥈", "🥉"]
    icons2 = ["😵", "😴", "🥱"]

    top_msg_lines = "\n".join(f"> - {icons[i]} **Топ {i+1}:** {member.mention} ({count})"for i, (member, count) in enumerate(most_active_msg))
    top_popular_ch = "\n".join(f"> - {icons[i]} **Топ {i+1}:** {ch.mention} ({count})"for i, (ch, count) in enumerate(most_popular))
    top_least_ch = "\n".join(f"> - {icons2[i]} **Топ {i+1}:** {ch.mention} ({count})"for i, (ch, count) in enumerate(least_popular))


    activity_embed = discord.Embed(
    title="Активность",
    description=(f"## Каналы:\n### Самые популярные:\n{top_popular_ch}\n### Самые непопулярные:\n{top_least_ch}\n\n## Игроки:\n### Самые активные по сообщениям:\n{top_msg_lines}"),
    timestamp=now
    )
    activity_embed.set_footer(text="Последнее обновление")

    global status_channel_id, status_message_id
    channel = guild.get_channel(status_channel_id)
    try: msg = await channel.fetch_message(status_message_id)
    except discord.NotFound: return
    old_embeds = msg.embeds
    roles_embed = old_embeds[0]
    await msg.edit(embeds=[roles_embed, activity_embed])

async def clear_all_dm_msg():
    deleted_total = 0

    for user in BOT.users:  # все пользователи, которых бот знает
        try:
            channel = await user.create_dm()  # получаем DM-канал
            async for message in channel.history(limit=100):  # можешь увеличить лимит
                if message.author == BOT.user:
                    try:
                        await message.delete()
                        deleted_total += 1
                    except Exception:
                        pass
        except Exception:
            continue
    print(f"Удалено {deleted_total} сообщений бота в ЛС пользователей")


async def build_roles_embed2():
    guild = BOT.get_guild(GUILD_ID)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    lines = []
    for item in ROLES_TO_TRACK_2:
        t = item["type"]

        #if t == "n|":
        #    lines.append('\n')
        #    continue

        if t == "line":
            members = await get_members(guild, item["roles"])
            role = guild.get_role(item["roles"])
            lines.append(f'{item["emoji"]} **{item["title"]}:** {members}\n')
            continue

        if t == "h0_2":
            #role = guild.get_role(item["roles"])
            lines.append(f'\n### {item["emoji"]} **{item["title"]}:**')
            continue

        if t == "block_rp":
            members = await get_members(guild, item["roles"])
            role = guild.get_role(item["roles"])
            lines.append(f'> - {item["emoji"]} {item["title"]}: {members}')
            continue

        if t == "h0_1":
            role = guild.get_role(item["roles"])
            lines.append(f'\n### {item["emoji"]} **{item["title"]}:**')
            continue

        if t == "block_dm":
            members = await get_members(guild, item["roles"])
            role = guild.get_role(item["roles"])
            lines.append(f'> - {item["emoji"]} {item["title"]}: {members}')    

    roles_embed = discord.Embed(
    title="Роли",
    description=f"\n".join(lines),
    timestamp=now
    )
    roles_embed.set_footer(text="Последнее обновление")
    
    global status_channel_id_2, status_message_id_2
    channel = guild.get_channel(status_channel_id_2)
    try:
        msg = await channel.fetch_message(status_message_id_2)
    except discord.NotFound:
        return
    old_embeds = msg.embeds
    activity_embed = old_embeds[1]
    await msg.edit(embeds=[roles_embed, activity_embed])

async def build_activity_embed2():
    guild = BOT.get_guild(GUILD_ID)
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    if not guild:
        return

    most_active_rep, least_active_rep = await get_most_active_members_by_reports(guild)
    #most_popular, least_popular = await get_channel_popularity(guild)
    #most_active_voice, voice_minutes = get_most_active_in_voice(guild)
    icons = ["🥇", "🥈", "🥉"]
    icons2 = ["💀", "👎", "💩"]

    top_active_rep = "\n".join(f"> - {icons[i]} **Топ {i+1}:** {member.mention} ({count})"for i, (member, count) in enumerate(most_active_rep))
    top_least_rep = "\n".join(f"> - {icons2[i]} **Топ {i+1}:** {member.mention} ({count})"for i, (member, count) in enumerate(least_active_rep))
    #top_popular_ch = "\n".join(f"> - {icons[i]} **Топ {i+1}:** {ch.mention} ({count})"for i, (ch, count) in enumerate(most_popular))
    #top_least_ch = "\n".join(f"> - {icons[i]} **Топ {i+1}:** {ch.mention} ({count})"for i, (ch, count) in enumerate(least_popular))


    activity_embed = discord.Embed(
    title="Активность",
    description=(f"## Игроки:\n### Самые активные по отчётам:\n{top_active_rep}\n### Самые неактивные по отчётам:\n{top_least_rep}"),
    timestamp=now
    )
    activity_embed.set_footer(text="Последнее обновление")

    global status_channel_id_2, status_message_id_2
    channel = guild.get_channel(status_channel_id_2)
    try:
        msg = await channel.fetch_message(status_message_id_2)
    except discord.NotFound:
        return
    old_embeds = msg.embeds
    roles_embed = old_embeds[0]
    await msg.edit(embeds=[roles_embed, activity_embed])

