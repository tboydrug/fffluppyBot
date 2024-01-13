import random
import disnake
import asyncio
import json
from disnake.ext import commands
from disnake.ext import tasks
from twitch import get_notifications
import sqlite3
import io
from config import ranks_img
from config import rank
from PIL import Image, ImageDraw, ImageFont


guild_id = 1025302660800315463
name_bot = 'fffluppy'
prefix = '!'
previous_message_date = None

start_role = 1025306938893934645
follower_role = 1025308526987460628
fan_role = 1025308355432042506


client = commands.Bot(command_prefix=prefix, intents=disnake.Intents.all())
client.remove_command('help')

connection = sqlite3.connect('server.db')
cursor = connection.cursor()


@client.event
async def on_ready():
    print('Bot connected')

    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        name TEXT,
        id INT,
        tw_id TEXT,
        coins INT,
        rep INT,
        rank INT,
        points INT
    )""")

    for guild in client.guilds:
        for member in guild.members:
            if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                cursor.execute(
                    "INSERT INTO users (name, id, tw_id, coins, rep, rank, points) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (member.name, member.id, 'NULL', 0, 0, 0, 0))
            else:
                pass

    connection.commit()

    server = client.fetch_guild(guild_id)

    for member in server.members:
        if 'Silver rank' in [role.name for role in member.roles]:
            user = await client.fetch_user(member.id)
            profile = await user.public_flags
            if user.public_flags



@client.event
async def on_button_click(interaction: disnake.MessageInteraction):
    if interaction.component.custom_id.startswith('role_button_'):
        role_id = int(interaction.component.custom_id.split('_')[2])
        role = disnake.utils.get(interaction.guild.roles, id=role_id)
        if role is not None:
            if role in interaction.author.roles:
                await interaction.author.remove_roles(role)
            else:
                await interaction.author.add_roles(role)

@client.command()
@commands.has_permissions(administrator=True)
async def role_button(ctx, role_id: int):
    await ctx.channel.purge(limit=1)
    role = disnake.utils.get(ctx.guild.roles, id=role_id)
    if role is not None:
        # Создаем объект кнопки
        button = disnake.ui.Button(style=disnake.ButtonStyle.green, label='НАЖМИ НА МЕНЯ', custom_id=f'role_button_{role_id}')
        # Создаем сообщение с кнопкой
        message = await ctx.send(
        embed=disnake.Embed(
        title="Уведомления о стримах",
        description=f"{role.mention}\n Узнавай первым когда начался стрим!",
        color=0x2F3136,)\
            .set_image(url="https://i.imgur.com/QzB7q9J.png")\
            .set_thumbnail("https://i.ibb.co/8BpPZC8/fc87a8e1-20fd-4ca0-85de-474117cd1adb-profile-image-70x70-round-2.png"), components=[disnake.ui.ActionRow(button)])
    else:
        message = await ctx.send('Такой роли не существует')


@client.command(name='test')
@commands.has_permissions(administrator=True)
async def test_command(ctx):
    channel_name = 'ChannelName'  # замените на имя канала
    channel_url = 'https://www.twitch.tv/fffluppy'  # замените на URL канала
    game = 'Game'  # замените на игру
    created_at = '2023-04-05T10:00:00Z'  # замените на дату начала трансляции
    role_id = disnake.utils.get(ctx.guild.roles, name="Iron rank")  # замените на ID роли, которой вы хотите упомянуть

    await ctx.send(
        content=role_id.mention,
        embed=disnake.Embed(
        title="СМОТРЕТЬ СТРИМ",
        description='Ваш любимый стример запустил трансляцию!',
        colour=0x6441A4,
        url='https://www.twitch.tv/imalwaysssad')\
        .set_thumbnail(url='https://i.ibb.co/8BpPZC8/fc87a8e1-20fd-4ca0-85de-474117cd1adb-profile-image-70x70-round-2.png')\
        .set_image(url='https://i.gifer.com/LRP3.gif')\
        .add_field(name="\🎮 DOTA 2", value="", inline=True)\
        .add_field(name='\🔴 54', value="", inline=True) \
        .add_field(name='\❤️ 1500', value="", inline=False) \
        .add_field(name='\🕙 2023.04.7:08:57', value="\n", inline=False))


@client.event
# Update members roles / Twitch Notification
async def on_member_update(before, after):
    role_to_check = disnake.utils.get(after.guild.roles, name="Silver rank")
    role_to_remove = disnake.utils.get(after.guild.roles, name="Copper rank")

    if role_to_check in after.roles and role_to_remove in after.roles:
        await after.remove_roles(role_to_remove)

    elif role_to_check not in after.roles and role_to_remove not in after.roles:
        await after.add_roles(role_to_remove)


@client.event
async def on_member_join(member):
    if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
        cursor.execute(
            "INSERT INTO users (name, id, tw_id, coins, rep, rank, points) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (member.name, member.id, 'NULL', 0, 0, 0, 0))
    else:
        pass

    connection.commit()

    role = disnake.utils.get(member.guild.roles, id=1025306938893934645)
    channel = member.guild.system_channel

    embed = disnake.Embed(
        title="",
        description=f"{member.name}#{member.discriminator}",
        color=0xffffff
    )

    await member.add_roles(role)
    await channel.send(embed=embed)


@client.command()
@commands.has_permissions(administrator=True)
# Показывает профиль участника
async def profile(ctx):
    await ctx.channel.purge(limit=1)
    # Загрузка изображения
    img = Image.open('image.png').convert('RGBA')
    rank_img = Image.open(ranks_img[cursor.execute("SELECT rank FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]])

    # Добавление текста на изображение
    draw = ImageDraw.Draw(img)

    # Настройки текста
    default_font = ImageFont.truetype("arial.ttf", size=30)
    font = ImageFont.truetype("D:/fonts/Decrypted.ttf", size=46)
    font2 = ImageFont.truetype("D:/fonts/Decrypted.ttf", size=30)

    # Twitch name
    text = f"""{cursor.execute("SELECT tw_id FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]}"""
    # Name
    text1 = f"{ctx.author.name}"
    # Level
    text2 = f"""RANK: {rank[cursor.execute("SELECT rank FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]]}"""
    # experience
    text3 = f"""POINTS: {cursor.execute("SELECT points FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]}"""
    # reputation
    text4 = f"""REP: {cursor.execute("SELECT rep FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]}"""
    # balance
    text5 = f"""FLUPYCOIN: {cursor.execute("SELECT coins FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]}"""

    # Draw text TW_NAME
    text_width, text_height = draw.textsize(text1, font=font)
    draw.text(((img.width - text_width) // 2, img.height - text_height - 200), text, font=font, fill=(0, 0, 0))
    # Draw text NAME
    text_width, text_height = draw.textsize(text1, font=font)
    draw.text(((img.width - text_width) // 2, img.height - text_height - 145), text1, font=font, fill=(0, 0, 0))
    # Draw text RANK
    draw.text((35, 325), text2, font=font2, fill=(0, 0, 0))
    # Paste image RANK
    img.paste(rank_img, (250, 325), mask=rank_img.split()[3])
    # Draw text POINTS
    draw.multiline_text((35, 340), text3, font=font2, fill=(0, 0, 0))
    # Draw text REP
    draw.text((35, 400), text4, font=font2, fill=(0, 0, 0))
    # Draw text FLUPYCOIN
    draw.multiline_text((160, 400), text5, font=font2, fill=(0, 0, 0))

    # Создание буфера для изображения в памяти
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    # Создание и отправка сообщения с изображением
    file = disnake.File(img_buffer, filename='image.png')
    await ctx.send(file=file)


@client.command()
@commands.has_permissions(administrator=True)
# Clear messages
async def clear(ctx, amount=1):
    await ctx.channel.purge(limit=amount)


# Twitch
@tasks.loop(seconds=10)
async def check_twitch_online_streamers():
    global previous_message_date
    channel = await client.fetch_channel(conf["twitch_discord_channel"])

    print("Check stream")
    notifications = get_notifications()

    if len(notifications) > 0:
        if notifications[0]['formatted_date'] == previous_message_date:
            return

    print(notifications)
    if channel is not None and bool(notifications):
        await channel.send(
            content=f"<@&{fan_role}>",
            embed=disnake.Embed(
                title="СМОТРЕТЬ СТРИМ",
                description=notifications[0]['imalwaysssad']['title'],
                colour=0x6441A4,
                url='https://www.twitch.tv/fffluppy') \
                .set_thumbnail(
                url="https://static-cdn.jtvnw.net/jtv_user_pictures/fc87a8e1-20fd-4ca0-85de-474117cd1adb-profile_image-70x70.png") \
                .add_field(name=f"\🎮 {notifications[0]['imalwaysssad']['game_name']}", value="", inline=True) \
                .add_field(name=f"\🔴 {notifications[0]['imalwaysssad']['viewer_count']}", value="", inline=True) \
                .add_field(name=f"\❤️ {notifications[0]['total']}", value="", inline=False) \
                .set_footer(text=notifications[0]['formatted_date']))

        previous_message_date = notifications[0]['formatted_date']
    else:
        print(f"Канал с ID {channel} не найден или стример офлайн.")


with open("conf.json") as conf_file:
    conf = json.load(conf_file)

if __name__ == "__main__":
    check_twitch_online_streamers.start()
    client.run(conf["discord_token"])

