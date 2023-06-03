import discord
import responses
import myinfo
import asyncio
from discord.ext import commands

async def send_message(message):
    try:
        response = await responses.handle_response(message)  # Pass 'message.channel'
        if response == None:
            return
        await message.channel.send(response)
    except Exception as e:
        print(e)

def run_discord_bot():
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} is now running')
    
    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        
        username = str(message.author)
        user_message = str(message.content)
        channel = str(message.channel)
    
        print(f"{username} said '{user_message}' ({channel})")

        if user_message[0] == '!':
            user_message = user_message[1:]
            await send_message(message)

    client.run(myinfo.TOKEN)

async def SendMessage(results, message):
    print(f"Results are: {results}")
    await message.channel.send(results)
    print("Sent results")