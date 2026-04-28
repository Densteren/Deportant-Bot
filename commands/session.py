from discord import app_commands
from collections import Counter
from dataclasses import dataclass
from io import StringIO
import discord, aiohttp, json
from main import BOT



@dataclass(frozen=True)
class BlockPos:
    x: int
    y: int
    z: int
    dim: int

@dataclass
class Row:
    x: int
    y: int
    z: int
    dim: int
    action: int
    block: str | None
    state: dict
    replaced_block: str | None
    replaced_state: dict | None
    unix: int

async def read_from_text(text: str):
    for line in StringIO(text):
        json_array = json.loads(line)

        if len(json_array) not in (8, 10):
            continue

        x, y, z, dim, action = json_array[:5]
        block_id = json_array[5]
        state = json_array[6]

        replaced_block = None
        replaced_state = None
        unix_index = 7

        if len(json_array) > 8:
            replaced_block = json_array[7]
            replaced_state = json_array[8]
            unix_index = 9

        unix = json_array[unix_index]

        yield Row(
            x, y, z, dim,
            action,
            block_id,
            state,
            replaced_block,
            replaced_state,
            unix
        )


@app_commands.command(name="session", description="проверить .bs файл")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(файл="cсылка на .bs файл (cdn.discordapp.com/attachments)")
async def session(interaction: discord.Interaction, файл: str):
    await interaction.response.defer(ephemeral=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(файл) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Ошибка скачивания файла.")
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

        message = (
            f"Фактически установлено блоков: {len(block_map)}\n"
            f"Всего установлено: {placed}\n"
            f"Всего сломано: {removed}\n"
            f"Пустые строки: {nulls}\n\n"
            "Поставленные блоки (топ 50):\n"
        )

        for block, count in list(sorted_result.items()):
            clean_name = block.replace("minecraft:", "")[:50]
            message += f"{clean_name} — {count}\n"
        
        dimension_names = {1: "Обычный мир", 2: "Ад", 3: "Энд"}
        message += "\nИзмерения:\n"
        for dim, count in dim_counter.items():
            name = dimension_names.get(dim, f"Неизвестное измерение ({dim})")
            message += f"{name} — {count}\n"

        await interaction.followup.send(f"```{message}```")

    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}")
