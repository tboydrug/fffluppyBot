from keep_alive import keep_alive
import subprocess
import boto3
import botocore.exceptions
import disnake
# from disnake import Permissions
import json
from disnake.ext import commands
from disnake.ext import tasks
import twitch 
import sqlite3
import io
import asyncio
from config import ranks_img
from config import rank
from config import gifs
from PIL import Image, ImageDraw, ImageFont
import time
import random
from colormath.color_objects import sRGBColor
#from colormath.color_diff import delta_e_cie1976

guild_id = 1057408057426067526
logs_id = 1111651191919743008 
name_bot = 'fffluppy'
prefix = '/'

start_role = 1090194970050318356
follower_role = 1057413976570462298

client = commands.Bot(command_prefix=prefix, help_command=None, intents=disnake.Intents.all(), test_guilds=[1057408057426067526])

s3 = boto3.client('s3', aws_access_key_id='AKIAVFVCOP3XTVF52O4R', aws_secret_access_key='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')
bucket_name = 'fffluppy-server'



ROLES_TO_CHANGE = [
    {'role_id': 1102249945207160903, 'colors': ['#020202', '#fa0000', '#d38f4c', '#f8fa00', '#4caf2d', '#00ffe9', '#374ac0', '#d666cc']}
]

async def is_valid_sqlite_database():
    try:
        s3.head_object(Bucket=bucket_name, Key='server.db')
        print("База данных найдена")
        return True
    except Exception as e:
        print(f"Не удалось найти базу данных. Ошибка: {str(e)}")
        return False
#    try:
#        s3.download_file(bucket_name, 'server.db', 'server.db')
#        print('База данных не повреждена')
#        s3_object = io.BytesIO()
#        s3.download_fileobj(bucket_name, 'server.db', s3_object)
#        s3_object.seek(0)
#        connection = sqlite3.connect(':memory:')
#        cursor = connection.cursor()
#        connection.execute("SELECT * FROM sqlite_master")
#        print('База данных не повреждена')
#        return True
#    except sqlite3.Error as e:
#        # Если произошла ошибка, файл не является корректной базой данных SQLite
#        print(f"Файл не является корректной базой данных SQLite. Ошибка: {str(e)}")
#        return False
#    finally:
#        if 'connection' in locals():
#            try:
#                connection.close()
#            except NameError:
#                pass

@client.event
async def on_ready():
    print('Bot connected')
    # bot_user = await client.fetch_user(client.user.id)
    # with open('killua.png', 'rb') as f:
    #   avatar = f.read()
    # await client.user.edit(avatar=avatar)

    # Попробуем загрузить файл с Amazon S3
    try:
        if is_valid_sqlite_database():
            s3_object = io.BytesIO()
            s3.download_fileobj(bucket_name, 'server.db', s3_object)
            s3_object.seek(0)
            connection = sqlite3.connect(':memory:')
            cursor = connection.cursor()
        else:
            print(f"Не удалось найти базу данных. Переходим к инициализации. Ошибка: {str(e)}")
            # Если файла нет, используем код для работы с дисковым файлом
            connection = sqlite3.connect('server.db')
            cursor = connection.cursor()
            
        cursor.execute("""CREATE TABLE IF NOT EXISTS users(
            name TEXT,
            id INT,
            tw_id TEXT,
            coins INT,
            rep INT,
            rank INT,
            points INT
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS roles(
            role_id INT, 
            role_name TEXT, 
            color TEXT, 
            created_at INT
        )""")
        
        for guild in client.guilds:
            for member in guild.members:
                if member.discriminator is None:
                    username = f"{member.name}#{member.discriminator}"
                else:
                    username = member.name
                if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                    cursor.execute(
                        "INSERT INTO users (name, id, tw_id, coins, rep, rank, points) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (username, member.id, 'NULL', 0, 0, 0, 0))
                else:
                    cursor.execute(f"UPDATE users SET name = ? WHERE id = {member.id}", (username,))
                print("База данных обновлена")
    
        connection.commit()
    
        cursor.execute("SELECT * FROM users")
        data = cursor.fetchall()
    
        print(f"данные для форматирования базы данных {data}")
        # Создаем io.BytesIO объект и записываем в него содержимое базы данных
        s3_object = io.BytesIO()
    
        output = subprocess.check_output(['sqlite3', 'server.db', '.dump'], text=True)
        s3_object.write(output.encode('utf-8'))
        # Переместите указатель файла в начало перед чтением
        s3_object.seek(0)
        # Загружаем файл базы данных на Amazon S3
        s3.upload_fileobj(s3_object, bucket_name, 'server.db')
    except Exception as e:
        print(f"Не удалось инициализировать базу данных. Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            try:
                connection.close()
                print("База данных инициализирована.")
            except NameError:
                pass

    if is_valid_sqlite_database():
        if remove_expired_roles.is_running():
            remove_expired_roles.cancel()
            print("remove_expired_roles отменено")

        try:
            remove_expired_roles.start()
            #change_color.start()
        except NameError:
            pass
    
    guild = client.get_guild(guild_id)

# @client.command()
# @commands.has_permissions(administrator=True)
# # async def send(ctx):
# #     channel = await client.fetch_channel(conf["twitch_reward_channel"])
# #     await ctx.channel.purge(limit=1)
# #     await ctx.send(content="@everyone",
# #         embed=disnake.Embed(
# #             title="Добавлен магазин ролей",
# #             description=f"Теперь вы можете переводить флюпики с твича в дискорд и покупать на них кастомные временные роли, а также выделять их в списке участников. Для взаимодействия с ботом используйте `{prefix}` в канале {channel.mention}"
# #     ).add_field(name="", value="флюпики могут начислиться не сразу"))


@client.command()
async def test(ctx):
    author = ctx.message.author

    try:
        connection = sqlite3.connect('server.db')
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM users WHERE id = ?", (author.id,))
        result = cursor.fetchone()
    
        if result:
            name = result[0]
            message = f"Привет, {name}!"
        else:
            message = "Твое имя не найдено в базе данных."
    except Exception as e:
        print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            try:
                connection.close()
            except NameError:
                pass
        
    await ctx.send(message)
  

@tasks.loop(hours=24)
async def change_color():
    await client.wait_until_ready()
    for role_info in ROLES_TO_CHANGE:
        guild = disnake.utils.get(client.guilds, id=guild_id)
        role = disnake.utils.get(guild.roles, id=role_info['role_id'])
        print(role)
        if role:
            colors = role_info['colors']
            current_color = role.color
            print("set color")
            next_color_index = (colors.index(str(current_color))) + 1
            if next_color_index >= len(colors):
                next_color_index = 0
            new_color = disnake.Color(int(colors[next_color_index][1:], 16))
            await role.edit(color=new_color)
            print(f'Changed color of role {role.name} to {new_color}')


@client.slash_command(description="основные команды")
async def команды(ctx):
    embed = disnake.Embed(title="Команды")

    embed.add_field(name=f'{prefix}баланс', value='Ваше количество флюпиков')
    embed.add_field(name=f'{prefix}магазин', value='Да магазин')

    await ctx.send(embed=embed)


@client.slash_command(description="Магазин кто не понял")
async def магазин(ctx):
    await ctx.channel.purge(limit=1)
    embed1 = disnake.Embed(title="Персональная роль на месяц", description=f"`{prefix}купить_роль` название цвет\n🪙 5000\nПример: `{prefix}купить_роль` негр 020202")
    embed2 = disnake.Embed(title="Выделить вашу роль", description=f"`{prefix}выделить_роль` id \n🪙 5000\nПример: `{prefix}выделить_роль` 1234567890111234567\n \n`Нажмите правой кнопкой мыши по роли, со включенным режимом разработчика чтобы копировать id (Настройки-> Расширенные)`")
    await ctx.send(embeds=[embed1, embed2])


@client.slash_command(description="Выводит ваше количество флюпиков")
async def баланс(ctx):
    await ctx.channel.purge(limit=1)
    user_id = str(ctx.author.id)

    s3_object = io.BytesIO()
    s3.download_fileobj(bucket_name, 'server.db', s3_object)

    s3_object.seek(0)

    try:
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
    
        cursor.executescript(s3_object.read().decode('utf-8'))
        
        cursor.execute(f"SELECT coins FROM users WHERE id = '{user_id}'")
        result = cursor.fetchone()
    
        embed = disnake.Embed(title="Баланс")
        embed.add_field(name=f"У вас 🪙 {result[0]}", value="\n Чтобы пополнить баланс воспользуйтесь переводом флюпиков на твиче")
    except Exception as e:
        print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            try:
                connection.close()
            except NameError:
                pass
        
    await ctx.send(embed=embed)


@client.command()
@commands.has_permissions(administrator=True)
async def add_coins(ctx, member: disnake.Member, count: int):
    await ctx.channel.purge(limit=1)
    user_id = str(member.id)

    try:
        connection = sqlite3.connect('server.db')
        cursor = connection.cursor()
        cursor.execute(f"UPDATE users SET coins = coins + '{count}' WHERE id = '{user_id}'")
        connection.commit()
    
        cursor.execute("SELECT * FROM users")
        data = cursor.fetchall()
    
        s3_object = io.BytesIO()
        
        output = subprocess.check_output(['sqlite3', 'server.db', '.dump'], text=True)
        s3_object.write(output.encode('utf-8'))
    
        s3_object.seek(0)
    
        s3.upload_fileobj(s3_object, bucket_name, 'server.db')
    except Exception as e:
        print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            try:
                connection.close()
            except NameError:
                pass
        
    print(f"{ctx.author.mention} начислил {member.mention} {count} флюпиков")


async def create_role(guild, role_name, duration, colour):
    if role_name != cursor.execute("SELECT role_name FROM roles WHERE role_name = ?", (role_name,)).fetchone():
        role = await guild.create_role(name=role_name, color=colour)
        print("Роль создана")
        created_at = int(time.time())

        try:
            connection = sqlite3.connect('server.db')
            cursor = connection.cursor()
            cursor.execute(f"INSERT INTO roles (role_id, role_name, color, created_at) VALUES ({role.id}, '{role_name}', '{colour}', {created_at + duration})")
            connection.commit()
    
            cursor.execute("SELECT * FROM users")
            data = cursor.fetchall()
    
            s3_object = io.BytesIO()
            
            output = subprocess.check_output(['sqlite3', 'server.db', '.dump'], text=True)
            s3_object.write(output.encode('utf-8'))
    
            s3_object.seek(0)
    
            s3.upload_fileobj(s3_object, bucket_name, 'server.db')
        
            asyncio.create_task(remove_role(role.id, duration, created_at))
        except Exception as e:
            print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
        finally:
            if 'connection' in locals():
                try:
                    connection.close()
                except NameError:
                    pass
    else:
        print("Роль уже существует")


async def remove_role(role_id, duration, created_at):
    await asyncio.sleep(duration)
    guild = disnake.utils.get(client.guilds, id=guild_id)
    role = disnake.utils.get(guild.roles, id=role_id)
    current_time = int(time.time())
    if role and created_at + duration <= current_time:
        await role.delete()

    try:
        connection = sqlite3.connect('server.db')
        cursor = connection.cursor()
        cursor.execute(f"DELETE FROM roles WHERE role_id = {role_id}")
        connection.commit()
    
        cursor.execute("SELECT * FROM users")
        data = cursor.fetchall()
    
        s3_object = io.BytesIO()
        
        output = subprocess.check_output(['sqlite3', 'server.db', '.dump'], text=True)
        s3_object.write(output.encode('utf-8'))
    
        s3_object.seek(0)
    
        s3.upload_fileobj(s3_object, bucket_name, 'server.db')
    except Exception as e:
        print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            try:
                connection.close()
            except NameError:
                pass

@client.slash_command(description="Кастомная роль, которая НЕ отображается отдельно в списке участников")
async def купить_роль(ctx, name: str, colour: str = '020202'):
    print(f"{ctx.author.name} хочет купить роль '{name}' с цветом '{colour}'")
    # проверяем правильность формата цвета
    try:
        # Проверка правильности ввода цвета
        sRGBColor.new_from_rgb_hex(colour)
    except ValueError:
        await ctx.send(f"{ctx.author.mention}, неверный формат цвета. Введите цвет в формате HEX, например: 020202")
        return
      
    # colour_int = int(colour, 16)
    user_id = str(ctx.author.id)
    
    s3_object = io.BytesIO()
    s3.download_fileobj(bucket_name, 'server.db', s3_object)

    s3_object.seek(0)

    try:
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
    
        cursor.executescript(s3_object.read().decode('utf-8'))
        cursor.execute(f"SELECT coins FROM users WHERE id = '{user_id}'")
        balance = cursor.fetchone()[0]
    except Exception as e:
        print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            try:
                connection.close()
            except NameError:
                pass

    
    # проверка наличия достаточного количества денег у пользователя
    if balance >= 5000:
        # создаем роль
        await create_role(ctx.guild, name, 2592000, disnake.Colour(int(colour, 16)))  # 2592000 - 30 дней в секундах
        role = disnake.utils.get(ctx.guild.roles, name=name)
        existing_role = disnake.utils.get(ctx.guild.roles, name='Керринг машина')
        if existing_role:
            position = existing_role.position -1
        await role.edit(position=position)
        # присваиваем роль пользователю
        print("выдаём роль челу")
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention}, роль '{name}' успешно куплена за 5000 монет.")
        # вычитаем стоимость роли из баланса пользователя
        try:
            connection = sqlite3.connect('server.db')
            cursor = connection.cursor()
            cursor.execute(f"UPDATE users SET coins = coins - 5000 WHERE id = '{user_id}'")
            connection.commit()
    
            cursor.execute("SELECT * FROM users")
            data = cursor.fetchall()
    
            s3_object = io.BytesIO()
            
            output = subprocess.check_output(['sqlite3', 'server.db', '.dump'], text=True)
            s3_object.write(output.encode('utf-8'))
    
            s3_object.seek(0)
    
            s3.upload_fileobj(s3_object, bucket_name, 'server.db')
        except Exception as e:
            print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
        finally:
            if 'connection' in locals():
                try:
                    connection.close()
                except NameError:
                    pass
    else:
        await ctx.send(f"{ctx.author.mention}, у вас недостаточно монет для покупки роли.")


@client.slash_command(description="Выделяет купленную ранне вами роль в списке участников над follower")
async def выделить_роль(ctx, role_id: str):
    user_id = str(ctx.author.id)
    cursor.execute(f"SELECT coins FROM users WHERE id = '{user_id}'")
    balance = cursor.fetchone()[0]

    # проверка наличия достаточного количества денег у пользователя
    if balance >= 5000:
        try:
            role_id = int(role_id)
        except ValueError:
            await ctx.send("ID роли должно быть числом")
            return

        role = disnake.utils.get(ctx.guild.roles, id=role_id)
        if not role:
            await ctx.send("Роль с таким ID не найдена.")
            return

        if cursor.execute(f"SELECT role_id FROM roles WHERE role_id = {role_id}").fetchone() is None:
            await ctx.send("У вас недостаточно прав чтобы поднять эту роль")
            return

        await role.edit(hoist=True)

        # вычитаем стоимость роли из баланса пользователя
        cursor.execute(f"UPDATE users SET coins = coins - 5000 WHERE id = '{user_id}'")

        await ctx.send(f"{ctx.author.mention}, роль '{role.name}' успешно выделена за 5000 флюпиков.")
    else:
        await ctx.send(f"{ctx.author.mention}, у вас недостаточно флюпиков.")


@tasks.loop(hours=24)
async def remove_expired_roles():
    print("remove role check")
    now = int(time.time())
    
    s3_object = io.BytesIO()
    s3.download_fileobj(bucket_name, 'server.db', s3_object)

    s3_object.seek(0)

    expired_roles = []
    
    try:
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
    
        cursor.executescript(s3_object.read().decode('utf-8'))
        
        cursor.execute("SELECT role_id, role_name, created_at FROM roles")
        expired_roles = cursor.fetchall()
    except Exception as e:
        print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            try:
                connection.close()
            except NameError:
                pass
                
    for expired_role in expired_roles:
        print("check role")
        role_id = expired_role[0]
        role_name = expired_role[1]
        created_at = expired_role[2]
        guild = disnake.utils.get(client.guilds, id=guild_id)
        role = disnake.utils.get(guild.roles, id=role_id)
        if role and created_at < now:
            channel = client.get_channel(logs_id)
            await role.delete()
            
            try:
                connection = sqlite3.connect('server.db')
                cursor = connection.cursor()
                cursor.execute(f"DELETE FROM roles WHERE role_id = {role_id}")
                connection.commit()
    
                cursor.execute("SELECT * FROM users")
                data = cursor.fetchall()
    
                s3_object = io.BytesIO()
    
                output = subprocess.check_output(['sqlite3', 'server.db', '.dump'], text=True)
                s3_object.write(output.encode('utf-8'))
    
                s3_object.seek(0)
    
                s3.upload_fileobj(s3_object, bucket_name, 'server.db')
            except Exception as e:
                print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
            finally:
                if 'connection' in locals():
                    try:
                        connection.close()
                    except NameError:
                        pass
            
            await channel.send(f"Role '{role_name}' deleted")


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
            .set_thumbnail("https://i.ibb.co/8BpPZC8/fc87a8e1-20fd-4ca0-85de-474117cd1adb-profile-image-70x70-round-2.png"), components=[disnake.ui.ActionRow(button)])
    #else:
        # message = await ctx.send('Такой роли не существует')


@client.event
async def on_message_delete(message):
    channel = client.get_channel(logs_id)
    
    # Отправка содержимого удаленного сообщения в канал
    await channel.send(f"id: ```{message.author.mention}```\nName: {message.author.mention}\nDeleted message: ```{message.content}```\n")


@client.event
async def on_message_edit(before, after):
    channel = client.get_channel(logs_id)
    
    # Отправка обновленного содержимого сообщения в канал
    await channel.send(f"id: ```{before.author.mention}```\nName: {before.author.mention}\n```Before: {before.content}\nAfter: {after.content}```\n")


@client.event
# Update members roles / Twitch Notification
async def on_member_update(before, after):
    # before_username = f"{before.name}#{before.discriminator}"
    if after.discriminator is not None:
        after_username = f"{after.name}#{after.discriminator}"
    else:
        after_username = after.name
    role_to_remove = disnake.utils.get(after.guild.roles, name="unknown")

    after_without_roles = [role for role in after.roles if role != after.guild.default_role]
    if not after_without_roles:
        await after.add_roles(role_to_remove)
    else:
        before_with_role_to_remove = [role for role in before.roles if role == role_to_remove]
        if role_to_remove in before_with_role_to_remove:
            await after.remove_roles(role_to_remove)
            
    s3_object = io.BytesIO()
    s3.download_fileobj(bucket_name, 'server.db', s3_object)

    s3_object.seek(0)
    try:
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
    
        cursor.executescript(s3_object.read().decode('utf-8'))
        
        before_name = cursor.execute(f"SELECT name FROM users WHERE id = {before.id}").fetchone()
        if before_name != after_username:
            if cursor.execute(f"SELECT id FROM users WHERE id = {before.id}").fetchone():
                cursor.execute("UPDATE users SET name = ? WHERE id = ?", (after_username, before.id))
                print(f"{before_name} изменил имя на {after.name}")
                connection.commit()
    
                cursor.execute("SELECT * FROM users")
                data = cursor.fetchall()
    
                s3_object = io.BytesIO()
                
                output = subprocess.check_output(['sqlite3', 'server.db', '.dump'], text=True)
                s3_object.write(output.encode('utf-8'))
    
                s3_object.seek(0)
    
                s3.upload_fileobj(s3_object, bucket_name, 'server.db')
    except Exception as e:
        print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            try:
                connection.close()
            except NameError:
                pass

@client.event
async def on_member_join(member):
    if member.discriminator is not None:
        username = f"{member.name}#{member.discriminator}"
    else:
        username = member.name
        
    s3_object = io.BytesIO()
    s3.download_fileobj(bucket_name, 'server.db', s3_object)

    s3_object.seek(0)
    
    try:
        connection = sqlite3.connect(':memory:')
        cursor = connection.cursor()
    
        cursor.executescript(s3_object.read().decode('utf-8'))
        
        if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
            cursor.execute("INSERT INTO users (name, id, tw_id, coins, rep, rank, points) VALUES (?, ?, ?, ?, ?, ?, ?)", (username, member.id, 'NULL', 0, 0, 0, 0))
        else:
            pass
    
        connection.commit()
    
        cursor.execute("SELECT * FROM users")
        data = cursor.fetchall()
    
        s3_object = io.BytesIO()
        
        output = subprocess.check_output(['sqlite3', 'server.db', '.dump'], text=True)
        s3_object.write(output.encode('utf-8'))
    
        s3_object.seek(0)
    
        s3.upload_fileobj(s3_object, bucket_name, 'server.db')
    except Exception as e:
        print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
    finally:
        if 'connection' in locals():
            try:
                connection.close()
            except NameError:
                pass

    role = disnake.utils.get(member.guild.roles, id=1090194970050318356)

    await member.add_roles(role)


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
    # default_font = ImageFont.truetype("./fonts/ARIAL.TTF", size=30)
    font = ImageFont.truetype("./fonts/Decrypted.ttf", size=46)
    font2 = ImageFont.truetype("./fonts/Decrypted.ttf", size=30)

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


@client.slash_command(description="проверить перевод")
async def перевод(ctx):
    channel = await client.fetch_channel(conf["twitch_reward_channel"])
    rewards = twitch.get_redemption_reward()
    guild = client.get_guild(guild_id)

    if channel is not None and bool(rewards):
        for reward in rewards['data']:

            s3_object = io.BytesIO()
            s3.download_fileobj(bucket_name, 'server.db', s3_object)

            s3_object.seek(0)
            try:
                connection = sqlite3.connect(':memory:')
                cursor = connection.cursor()
    
                cursor.executescript(s3_object.read().decode('utf-8'))
    
                if cursor.execute(f"SELECT id FROM users WHERE name = '{reward['user_input']}'").fetchone():
                    status = "FULFILLED"
                    cursor.execute(f"UPDATE users SET coins = coins + {reward['reward']['cost']} WHERE name = '{reward['user_input']}'")
                    connection.commit()
    
                    cursor.execute("SELECT * FROM users")
                    data = cursor.fetchall()
    
                    s3_object = io.BytesIO()
                    
                    output = subprocess.check_output(['sqlite3', 'server.db', '.dump'], text=True)
                    s3_object.write(output.encode('utf-8'))
    
                    s3_object.seek(0)
    
                    s3.upload_fileobj(s3_object, bucket_name, 'server.db')
                    
                    twitch.update_redemption_status(reward['id'], status)
                    member = guild.get_member_named(reward['user_input'])
                    await channel.send(f"{reward['user_login']} перевёл флюпики {member.mention}")
                else:
                    status = "CANCELED"
                    twitch.update_redemption_status(reward['id'], status)
                    await ctx.send("введённого имени нет или оно некорректно")
                    print({reward['user_input']})
                
            except Exception as e:
                print(f"Не удалось подключиться к базе данных. Ошибка: {str(e)}")
            finally:
                if 'connection' in locals():
                    try:
                        connection.close()
                    except NameError:
                        pass

    else:
        await ctx.send(f"Канал с ID {channel} не найден или нет невыполненных наград.")


@client.event
async def on_message(message):
    # Проверьте, чтобы бот не реагировал на свои собственные сообщения, чтобы избежать бесконечных циклов
    if message.author == client.user:
        return

    # Получите объект сервера
    server = message.guild

    # Проверьте, является ли автор сообщения владельцем сервера
    if message.author == server.owner or message.author.id == 507991914327310337:
        if 'https://www.twitch.tv/fffluppy' in message.content.lower():
            await message.delete(),
            await stream(message)

    # Полезные действия бота здесь

    await client.process_commands(message)


# Twitch
async def stream(message):
  
    #channel = client.get_channel(conf["twitch_notification_channel"])

    print("Check stream")
    notifications = twitch.get_notifications()
          
    if bool(notifications):
        message_sent = await message.channel.send(
            content="@everyone",
            embed=disnake.Embed(
                title="СМОТРЕТЬ СТРИМ",
                description=notifications[0]['fffluppy']['title'],
                colour=0x6441A4,
                url='https://www.twitch.tv/fffluppy') \
                .set_thumbnail(
                url='https://i.ibb.co/8BpPZC8/fc87a8e1-20fd-4ca0-85de-474117cd1adb-profile-image-70x70-round-2.png') \
                .set_image(random.choice(gifs)) \
                .add_field(name=f"\🎮 {notifications[0]['fffluppy']['game_name']}", value="", inline=True) \
                .add_field(name=f"\🔴 {notifications[0]['fffluppy']['viewer_count']}", value="", inline=True) \
                .add_field(name=f"\❤️ {notifications[0]['total']}", value="", inline=False) \
                .add_field(name=f"\🕙 {notifications[0]['formatted_date']}", value="", inline=False))

        if message_sent:
            activity = disnake.Activity(
                type=disnake.ActivityType.streaming,
                name='fffluppy',
                url='https://www.twitch.tv/fffluppy',
                game=notifications[0]['fffluppy']['game_name']
            )
            await client.change_presence(activity=activity)
      
    else:
        activity = disnake.Activity(
          type=disnake.ActivityType.playing,
          name=f'{prefix}команды'
        )
        await client.change_presence(activity=activity)
        await message.channel.send("fffluppy офлайн")
        

with open("conf.json") as conf_file:
    conf = json.load(conf_file)

  
if __name__ == "__main__":
    keep_alive()
    client.run(conf["discord_token"])
