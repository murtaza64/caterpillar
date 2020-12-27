# bot.py
import os

import discord
from dotenv import load_dotenv
import pickle
import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GAMES_FILE = 'games.pickle'


client = discord.Client()

games = pickle.load(open(GAMES_FILE, 'rb'))


def load_game(id_):
    try: 
        return games[id_]
    except KeyError:
        return None

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    for guild in client.guilds:
        print(guild.name)

    # print(
    #     f'{client.user} is connected to the following guild:\n'
    #     f'{guild.name}(id: {guild.id})'
    # )

@client.event
async def on_message(message):
    if client.user in message.mentions:
        if 'fake' in message.content:
            game = {'creator': message.author, 'players': set(), 'round_number': 0}
            msg = await message.channel.send('Ok, let\'s start a game of Fake Artist! Join by reacting with hand, and press the green button to start.')
            await msg.add_reaction('✋')
            await msg.add_reaction('🟢')
            game['join_message'] = msg
            games[message.channel] = game

@client.event
async def on_reaction_add(reaction, user):
    # print('reaction add!')
    if user == client.user:
        return
    for channel, game in games.items():
        if reaction.message == game['join_message']: 
            # print('found message!')
            mode = 0
            break
        if 'next_round_message' in game and reaction.message == game['next_round_message']:
            mode = 1
            break
    else:
        return

    if reaction.emoji == '✋':
        if mode == 0:
            game['players'].add(user)
        else:
            game['players'].add(user)
            await channel.send(f'Stay tuned {user.mention}, you\'ll be in the next round.')
    if reaction.emoji == '🚫':
        game['players'].remove(user)
        await channel.send(f'Alright {user.mention}, we\'ll see you later.')
    if reaction.emoji == '🟢':
        print(reaction.message.reactions)
        if [r for r in reaction.message.reactions if r.emoji == '🟢'][0].count > 2:
            return
        if mode == 0:
            await channel.send('Alright, let\'s get going!')
            await start_round(channel)
        else:
            await start_round(channel)

# @client.event
# async def on_reaction_remove(reaction, user):
#     print('reaction remove!')
#     if user == client.user:
#         return
#     for channel, game in games.items():
#         if reaction.message == game['join_message']: 
#             # print('found message!')
#             mode = 0
#             break
#         if game['next_round_message'] and reaction.message == game['next_round_message']:
#             mode = 1
#             break
#     else:
#         return

#     if reaction.emoji == '✋':
#         print('player lowered hand')
#         if mode == 0:
#             game['players'].remove(user)
#         else:
#             game['players'].remove(user)
#             await channel.send(f'Alright {user.mention}, we\'ll see you later.')

@client.event
async def on_raw_reaction_remove(payload):
    print('raw reaction remove')
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = await client.fetch_user(payload.user_id)

    if user == client.user:
        return
    for channel_, game in games.items():
        if message == game['join_message']: 
            # print('found message!')
            mode = 0
            break
        if 'next_round_message' in game and message == game['next_round_message']:
            mode = 1
            break
    else:
        return
    print('found message')
    if payload.emoji.name == '✋':
        print('player lowered hand')
        if mode == 0:
            game['players'].remove(user)
        else:
            game['players'].remove(user)
            await channel.send(f'Alright {user.mention}, we\'ll see you later.')


async def start_round(channel):
    game = games[channel]
    if game['round_number'] > 0:
        await channel.send(f'**{game["word"]}** was the object and {game["impostor"].mention} was the impostor!')

    players = list(game['players'])

    if len(players) < 3:
        await channel.send('Hmm... there aren\'t enough players here.')
        txt = f'React to this message to join and hit the green button to start when we have at least three players.'
        if players:
            txt += '\n\nThese players are already in the game: '
            for player in game['players']:
                txt += player.mention + ' '
        msg = await channel.send(txt)
        await msg.add_reaction('✋')
        await msg.add_reaction('🟢')
        await msg.add_reaction('🚫')
        game['next_round_message'] = msg
        return

    impostor = random.choice(players)
    word = 'Lion'
    game['impostor'] = impostor
    game['word'] = word
    game['round_number'] += 1

    txt = f'**Round {game["round_number"]} started**. React to this message to start another round or join for the next round.'
    txt += '\n\nThese players are in the game (and this is the draw order): '
    for player in game['players']:
        txt += player.mention + ' '
    msg = await channel.send(txt)
    await msg.add_reaction('✋')
    await msg.add_reaction('🟢')
    await msg.add_reaction('🚫')
    game['next_round_message'] = msg

    for player in players:
        dm = player.dm_channel
        if dm is None:
            dm = await player.create_dm()
        if player == impostor:
            await dm.send('You are the fake artist! Convince them you know what they\'re drawing.')
        else:
            await dm.send(f'The object everyone is drawing is **{word}**. You are not the fake artist.')

    game['busy'] = False

client.run(TOKEN)

