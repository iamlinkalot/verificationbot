import requests
from requests.auth import HTTPBasicAuth
import random
import re
import random
import myinfo
import discord.client
from discord.ext import commands
import bot
import sqlite3

conn = sqlite3.connect('characters.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS characters (
        character_name TEXT PRIMARY KEY,
        verification_code TEXT,
        username TEXT
    )
''')
link_clean = 'https://medivia.online/api/public/player/'

async def handle_response(message) -> str:
    username = message.author
    p_message = message.content
    pattern = r"""[^a-zA-Z\s]"""
    p_message = re.sub(pattern, '', p_message)
    results = ""

    #Checking if command is !Verify
    if p_message.startswith('verify '):
        parts = p_message.split(' ', 1)

        #Checking if command is !verify <text>
        if len(parts) == 2:
            Character_Name = parts[1]

            #If Character not In our list
            found_verification_code = find_character_info(Character_Name)
            print(f"Found code was: {found_verification_code}")

            if found_verification_code is None:
                verification_code = random.randint(10000000000,9999999999999)
                responseBool = CharExists(Character_Name)

                #Character Doesn't Exist
                if responseBool == False:
                    results = f"Either I did a dumb or character '{Character_Name}' does not exist"
                    await bot.SendMessage(results, message)
                    return

                #Character exists, add to list
                print("2")
                cursor.execute('SELECT * FROM characters WHERE character_name = ?', (Character_Name,))
                existing_character = cursor.fetchone()
                if existing_character:
                    cursor.execute('UPDATE characters SET verification_code = ?, username = ? WHERE character_name = ?', (verification_code, str(username), Character_Name))
                else:
                    character = (Character_Name, verification_code, str(username))
                    cursor.execute('INSERT INTO characters VALUES (?, ?, ?)', character)
                conn.commit()
                results = f'{Character_Name} exists. Please change your website comment to the following: "{verification_code}", then wait 5 minutes and use the !verify <character name> command again. For an example check this link: https://i.gyazo.com/174bf1aad5a21799adf5f378e94d17a2.png'
                await bot.SendMessage(results, message)
            
            else: #Character is in our list

                #Checking if Character's Comment is the verification code
                checkCharResponse, player_comment, verification_code = await CheckChar(Character_Name, found_verification_code)
                if checkCharResponse == False:
                    await bot.SendMessage(f'I checked your comments looking for: "{verification_code}" but instead found: "{player_comment}"', message)
                    return
                
                #Changing User's roles to be Verified
                changeRolesResponse = await ChangeRoles(message)
                if changeRolesResponse == False:
                    results = "We failed to change your discord role to be verified."
                    await bot.SendMessage(results, message)
                    return

                #Changing User's name to be their ingame name
                nameChangeResponse = await NameChange(username, Character_Name)
                if nameChangeResponse == False:
                    results = "We failed to change your name."
                    await bot.SendMessage(results, message)
                    return
                
                results = "Success! You have been Verified and your name changed to your ingame name."
                await bot.SendMessage(results, message)
                
                sql = 'DELETE FROM characters WHERE character_name=?'
                try:
                    cursor.execute(sql, (Character_Name,))
                    conn.commit()
                except Exception as e:
                    print(f"Ran into error while deleting char from database: {e}")
                
                print(f"Removed {Character_Name} from database as they were fully validated.")

                return
            return
        return
    
    if p_message.startswith("remove "):
        if "admin" in [role.name.lower() for role in message.author.roles]:
            parts = p_message.split(' ', 1)

            #Checking if command is !verify <text>
            if len(parts) == 2:
                Character_Name = parts[1]

                sql = 'DELETE FROM characters WHERE character_name=?'
                cursor.execute(sql, (Character_Name,))
                conn.commit()

                results = f"You have deleted {Character_Name} from the database."
                await bot.SendMessage(results, message)
        else:
            results = f"You are not an admin."
            await bot.SendMessage(results, message)

    if p_message.startswith("deleteall"):
        if "admin" in [role.name.lower() for role in message.author.roles]:
            
            cursor.execute('DELETE FROM characters',)
            conn.commit()   

            results = f"You have cleared the whole database."
            await bot.SendMessage(results, message)
        else:
            results = f"You are not an admin."
            await bot.SendMessage(results, message)

    if p_message.startswith("showall"):
        if "admin" in [role.name.lower() for role in message.author.roles]:
            
            sql = cursor.execute('SELECT * FROM characters')
            for row in sql:
                results = results + str(row) + "\n"

            await bot.SendMessage(results, message)
        else:
            results = f"You are not an admin."
            await bot.SendMessage(results, message)

    if p_message.startswith("help") or p_message.startswith("Help") or p_message.startswith("commands") or p_message.startswith("Commands") :
        results = f"""
        These are the current existing commands: 
!verify <username> - used to verify your account.
!help - shows this list
\n**Admin Commands**
!remove <username> - removes a specific user from the database (only used if things get stuck)
!deleteall - used to completely delete the database
!showall - used to show all entries in the database
        """
        await bot.SendMessage(results, message)

    return

def find_character_info(username):
    cursor.execute('SELECT character_name, verification_code FROM characters WHERE character_name = ?', (username,))
    result = cursor.fetchone()
    if result:
        return result[1]
    return None

def CharExists(charname): #Check if a Character exists on Medivia's Website
    link_char = link_clean + charname
    print(link_char)

    data = requests.get(link_char, auth=HTTPBasicAuth(myinfo.accountname, myinfo.password)).json()

    if data == []:
        return False
    
    player_name = data['player']['name']
    print(player_name)

    if charname == player_name:
        return True, 
    return False


async def CheckChar(charname, verification_code): #Check if a Character's Comment matches our given Verification Code
    link_char = link_clean + charname
    print(link_char)

    data = requests.get(link_char, auth=HTTPBasicAuth(myinfo.accountname, myinfo.password)).json()
    player_comment = data['player']['comment']
    print(player_comment)
    print(verification_code)

    if verification_code != player_comment:
        return False, player_comment, verification_code
    print("6.3")
    return True, player_comment, verification_code


async def ChangeRoles(member):
    try:
        guild = member.guild
        role = discord.utils.get(guild.roles, name="Validated")
        print(role)
        await member.author.add_roles(role)
    except Exception as e:
        print(e)
        return False
    return True

async def NameChange(member, charname):
    try:
        await member.edit(nick=charname)
    except Exception as e:
        print(e)
        return False
    return True