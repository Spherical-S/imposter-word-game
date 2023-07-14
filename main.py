import json
import time
import random
import discord
from discord import Color
from discord.ext import commands
from discord import Guild, Member, Embed, Client, Intents
from discord.utils import get
from discord.ext.commands import BucketType
from discord import app_commands
import os
from discord.ext.commands import Bot
import asyncio
from dotenv import load_dotenv
import os

#Global Variables
linebreak = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
MY_GUILD = discord.Object(id=788942821683363880)
with open("words.json", "r") as f: #gather the possible words
    word_list = json.load(f)
lobbies = {} # {"message_id": lobby class}
number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]


# Client handler in order to sync the bot to its commands and start the bot
class aclient(discord.Client):
    #initialize the bot
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    #sync the bot
    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


# Class to help manage games
class lobby:
    # Decide the 2 words [everyone, imposter]
    def __init__(self, owner, og_message):
        self.owner = owner
        self.og_message = og_message
        self.players = []
        self.words = ["", ""]
        self.kick_list = {}
        self.imposter = None
        self.stage = 0  # 0 = players joining, 1 = players are playing, 2 = voting time, 3 = done
        self.voting_list = {}
        self.voting_num_to_user = {}

        #Select the random word and the imposters word
        word_choice = random.choice(word_list)
        self.words[0] = random.choice(word_choice)
        if self.words[0] == word_choice[0]:
            self.words[1] = word_choice[1]
        else:
            self.words[1] = word_choice[0]

    # Starts the game
    async def start_game(self):
        if len(self.players) < 3: # Make sure theres at least 3 players
            try:
                await self.owner.send("You need at least 3 players to start the game.")
            except:
                pass
            return

        # Randomize the order of players
        self.players = self.randomize_players()

        #Select the imposter and send their word
        self.imposter = random.choice(self.players)
        try:
            await self.imposter.send("The word is " + self.words[1])
        except:
            pass

        # Send the rest of the players their word
        for i in self.players:
            if i == self.imposter:
                continue
            try:
                await i.send("The word is " + self.words[0])
            except:
                pass

        self.stage = 1 #set the stage to players are playing

        # send the updated embed and add proper reactions
        embed = discord.Embed(title="Game started", description=f"Take turns saying one word that is related to the word I dm'd you.\n{self.owner}, react with ➡ to continue to voting.\n" + self.order_to_string(),
                              color=discord.Color.red())
        await self.og_message.edit(embed=embed)
        await self.og_message.clear_reactions()
        await self.og_message.add_reaction("➡")
        await self.og_message.add_reaction("❌")

    #sets up the voting process
    async def voting(self):
        self.stage = 2 #sets stage to voting time

        #creates the embeds description
        desc = ""
        count = 1
        for i in self.players:
            if i not in self.kick_list:
                desc += str(count) + ". " + i.name + "\n"
                self.voting_list[i] = [count, 0, i, False] #add all possible votes to the voting list [corresponding num, votes]
                self.voting_num_to_user[count] = i
                count += 1
        desc += "React with ➡ to end voting"

        #updates the embed and adds reactions
        embed = discord.Embed(title="Who is the imposter?", description=desc, color=discord.Color.red())
        await self.og_message.edit(embed=embed)
        await self.og_message.clear_reactions()
        for i in range(len(self.voting_list)):
            await self.og_message.add_reaction(number_emojis[i])
        await self.og_message.add_reaction("➡")
        await self.og_message.add_reaction("❌")

    #calculates the votes
    async def calculate_votes(self):
        # Find the user with the most amount of votes, and if theres a tie
        highest = []
        highest_num = -1
        for i in self.voting_list:
            if self.voting_list[i][1] > highest_num:
                highest_num = self.voting_list[i][1]
                highest.clear()
                highest.append(self.voting_list[i][2])
                continue
            if self.voting_list[i][1] == highest_num:
                highest.append(self.voting_list[i][2])

        # if there was no tie
        if len(highest) == 1:
            self.kick_list[highest[0]] = None # add the kicked person to the kick list

            # If kicker person is not imposter and there are still 3+ players left
            if highest[0] != self.imposter and len(self.players) - len(self.kick_list) != 2:
                self.stage = 1
                embed = discord.Embed(title=f"💀 {highest[0].name} was kicked. They were not the imposter. 💀", description=f"Take turns saying one word that is related to the word I dm'd you.\n{self.owner}, react with ➡ to continue to voting.\n" + self.order_to_string(),
                                      color=discord.Color.red())
                await self.og_message.edit(embed=embed)
                await self.og_message.clear_reactions()
                await self.og_message.add_reaction("➡")
                await self.og_message.add_reaction("❌")
                self.voting_list.clear()
                self.voting_num_to_user.clear()

            # If kicked person is not imposter but there is 2 people left (the imposter wins)
            elif highest[0] != self.imposter and len(self.players) - len(self.kick_list) == 2:
                self.stage = 3
                embed = discord.Embed(title=f"😈 {highest[0].name} was kicked. They were not the imposter! 😈", description=f"Since 2 people remain, the imposter wins!!! Congratulations {self.imposter}\nThe words were {self.words[0]} and {self.words[1]}.\nUse /start-game to start a new game.",
                                      color=discord.Color.red())
                await self.og_message.edit(embed=embed)
                await self.og_message.clear_reactions()
                lobbies.pop(self.og_message.id)

            # If the kicked person was the imposter
            elif highest[0] == self.imposter:
                self.stage = 3
                embed = discord.Embed(title=f"🎉 {highest[0].name} was kicked. They were the imposter! 🎉", description=f"{self.imposter} loses!\nThe words were {self.words[0]} and {self.words[1]}.\nUse /start-game to start a new game.",
                                      color=discord.Color.red())
                await self.og_message.edit(embed=embed)
                await self.og_message.clear_reactions()
                lobbies.pop(self.og_message.id)

        # if there was a tie, just move on the the next round and dont do anything
        else:
            self.stage = 1
            embed = discord.Embed(title=f"⚖ There was a tie! No one was kicked. ⚖", description=f"Take turns saying one word that is related to the word I dm'd you.\n{self.owner}, react with ➡ to continue to voting.\n" + self.order_to_string(),
                                  color=discord.Color.red())
            await self.og_message.edit(embed=embed)
            await self.og_message.clear_reactions()
            await self.og_message.add_reaction("➡")
            await self.og_message.add_reaction("❌")
            self.voting_list.clear()
            self.voting_num_to_user.clear()

    def randomize_players(self):
        new_list = []
        for i in range(len(self.players)):
            rand_index = random.randint(0, len(self.players)-1)
            new_list.append(self.players[rand_index])
            self.players.pop(rand_index)

        return new_list

    def order_to_string(self):
        order_string = ""

        for i in range(len(self.players)):
            if self.players[i] in self.kick_list:
                continue
            order_string += str(i+1) + ". " + self.players[i].name + "\n"

        return order_string


load_dotenv()
client = aclient(intents=discord.Intents.default())

#display a message when the bot is ready
@client.event
async def on_ready():
    print(linebreak)
    print("Imposter Word Game is now online!")
    print(f"Logged on as {client.user}")
    print(linebreak)
    await asyncio.sleep(1)


# Runs when a reaction is added to a message sent by the bot in the current session
@client.event
async def on_reaction_add(reaction, user):
    if reaction.emoji == "✅":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        for i in lobbies[reaction.message.id].players:
            if user == i:
                return

        if len(lobbies[reaction.message.id].players) == 8:
            user.send("The requested lobby is full. Sorry!")

        else:
            lobbies[reaction.message.id].players.append(user)

    if reaction.emoji == "❌":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if lobbies[reaction.message.id].owner == user:
            lobbies.pop(reaction.message.id)
            await reaction.message.delete()

    if reaction.emoji == "👍":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if lobbies[reaction.message.id].owner == user:
            await lobbies[reaction.message.id].start_game()

    if reaction.emoji == "➡":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if lobbies[reaction.message.id].stage == 1 and lobbies[reaction.message.id].owner == user:
            await lobbies[reaction.message.id].voting()
            return

        if lobbies[reaction.message.id].stage == 2 and lobbies[reaction.message.id].owner == user:
            await lobbies[reaction.message.id].calculate_votes()
            return

    if reaction.emoji == "1️⃣":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if user not in lobbies[reaction.message.id].voting_list:
            return

        if lobbies[reaction.message.id].voting_list[user][3]:
            return

        lobbies[reaction.message.id].voting_list[lobbies[reaction.message.id].voting_num_to_user[1]][1] += 1

    if reaction.emoji == "2️⃣":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if user not in lobbies[reaction.message.id].voting_list:
            return

        if lobbies[reaction.message.id].voting_list[user][3]:
            return

        lobbies[reaction.message.id].voting_list[lobbies[reaction.message.id].voting_num_to_user[2]][1] += 1

    if reaction.emoji == "3️⃣":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if user not in lobbies[reaction.message.id].voting_list:
            return

        if lobbies[reaction.message.id].voting_list[user][3]:
            return

        lobbies[reaction.message.id].voting_list[lobbies[reaction.message.id].voting_num_to_user[3]][1] += 1

    if reaction.emoji == "4️⃣":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if user not in lobbies[reaction.message.id].voting_list:
            return

        if lobbies[reaction.message.id].voting_list[user][3]:
            return

        lobbies[reaction.message.id].voting_list[lobbies[reaction.message.id].voting_num_to_user[4]][1] += 1

    if reaction.emoji == "5️⃣":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if user not in lobbies[reaction.message.id].voting_list:
            return

        if lobbies[reaction.message.id].voting_list[user][3]:
            return

        lobbies[reaction.message.id].voting_list[lobbies[reaction.message.id].voting_num_to_user[5]][1] += 1

    if reaction.emoji == "6️⃣":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if user not in lobbies[reaction.message.id].voting_list:
            return

        if lobbies[reaction.message.id].voting_list[user][3]:
            return

        lobbies[reaction.message.id].voting_list[lobbies[reaction.message.id].voting_num_to_user[6]][1] += 1

    if reaction.emoji == "7️⃣":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if user not in lobbies[reaction.message.id].voting_list:
            return

        if lobbies[reaction.message.id].voting_list[user][3]:
            return

        lobbies[reaction.message.id].voting_list[lobbies[reaction.message.id].voting_num_to_user[7]][1] += 1

    if reaction.emoji == "8️⃣":
        if (reaction.message.id not in lobbies) or (user == "Imposter#6944"):
            return

        if user not in lobbies[reaction.message.id].voting_list:
            return

        if lobbies[reaction.message.id].voting_list[user][3]:
            return

        lobbies[reaction.message.id].voting_list[lobbies[reaction.message.id].voting_num_to_user[8]][1] += 1


@client.tree.command(name="ping", description="test if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong")


@client.tree.command(name="start-game", description="start a game of imposter")
async def start_game(interaction: discord.Interaction):
    embed = discord.Embed(title="New Game", description=f"{interaction.user} started a new game!\nReact with the ✅ to join.\nReact with the 👍 to confirm and start the game.\nReact with ❌ to cancel this game at any time",
                          color=discord.Color.red())
    await interaction.response.send_message(embed=embed)
    embed_sent = await interaction.original_response()
    await embed_sent.add_reaction("✅")
    await embed_sent.add_reaction("👍")
    await embed_sent.add_reaction("❌")
    lobbies[embed_sent.id] = lobby(interaction.user, embed_sent)


client.run(os.getenv("IMPOSTER_TOKEN"))