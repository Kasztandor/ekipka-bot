import os
import sqlite3
import discord
import dotenv
from discord.ext import commands, tasks
from datetime import datetime, timedelta

dotenv.load_dotenv(".env")

##################
# Database stuff #
##################

tables = {"userinfo": ["int:uid", "str:birthday"]}

con = sqlite3.connect("db.db")
cur = con.cursor()

for table in tables:
    res = cur.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='userinfo';")
    if res.fetchone()[0] == 0:
        cur.execute("CREATE TABLE userinfo ("+", ".join(list(map(lambda x : x.split(":")[1] + " " + x.split(":")[0], tables[table])))+")")
        con.commit()
    else:
        res = cur.execute("PRAGMA table_info(userinfo);")
        existing_columns = [row[1] for row in res.fetchall()]
        
        for column in tables[table]:           
            if column.split(":")[1] not in existing_columns:
                cur.execute(f"ALTER TABLE userinfo ADD COLUMN {column.split(":")[1]} {column.split(":")[0]}")
                con.commit()

def updateUserInfo(uid, name, value):
    # Check if user exists
    cur.execute("SELECT * FROM userinfo WHERE uid = ?", (uid,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO userinfo (uid) VALUES (?)", (uid,))
        con.commit()
    # update collumn with name "name" with value
    cur.execute(f"UPDATE userinfo SET {name} = ? WHERE uid = ?", (value, uid))
    con.commit()

#updateUserInfo(4, "birthday", "01-04-2003")

###############
# Discord bot #
###############

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"GUILD_ID: {os.getenv('GUILD_ID')}")
    await bot.tree.sync(guild=discord.Object(id=os.getenv("GUILD_ID")))
    print("Bot synced")

@bot.tree.command(name="urodziny", description="Dodaj swoją datę urodzin w formacie dd-mm-yyyy")
async def urodziny(interaction: discord.Interaction, data_urodzenia: str):
    try:
        data_urodzenia = datetime.strptime(data_urodzenia, "%d-%m-%Y").date()
        updateUserInfo(interaction.user.id, "birthday", data_urodzenia.strftime("%d-%m-%Y"))
        await interaction.response.send_message(f"Urodziny ustawione na {data_urodzenia.strftime('%d-%m-%Y')}", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Podana data jest niepoprawna.", ephemeral=True)
        return

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

bot.run(os.getenv("TOKEN"))
