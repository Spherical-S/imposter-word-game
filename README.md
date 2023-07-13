# Imposter Word Game
This is a discord.py app that is meant to allow discord users to play the imposter word game. This project was inspired by Yanstar Studios "Undercover" game, also known as "Mr. White".

## Game Objective
Within the game, everyone who is participating is direct messaged a word. Everyone but one person in the game gets the same word. The odd one out is called the imposter. The imposter will get a word that is similar to the word everyone else got. The imposter does not know that they are the imposter. For the imposter, the objective is to not get voted out of the game for being the imposter. They must try to figure out what the word that everyone else got is, and pretend that they got that word as well.

## How to play
1.  Use the /start-game command to start the game
2.  Allow everyone to react to the green check mark emoji to particiapte (min 3, max 8 players)
3.  The creator of the game must click the thumbs up reaction to start the game
4.  Everyone will be DM'd a word
5.  Everyone in the groupchat must take turns saying a word that is similar or relates to their word, but does not give away the word to the potential imposter
6.  After everyone has had their turn, the creator of the game clicks the arrow reaction to commence the voting process
7.  Everyone uses the reactions to vote who they think the imposter is (if there is a tie, nothing happens and you proceed to the next round)
8.  The bot will let everyone know if they kicked out the imposter.
9.  If the imposter is kicked out, everyone else wins, if the imposter is left with one other person, the imposter wins.

## Notes
- Sometimes if you react too early your reaction will not be seen by the bot. Always wait until all reactions are set up by the bot before you react. You may unreact and rereact if you think you reacted too early
- The words are contained in words.json, if you want to add new words just add them anywhere in the middle of the json file in this format: ["word 1", "word 2"].
- If you are the creator of the original "Undercover" game and would like me to change something or take this project down, please feel free to contact me @ sadiq.shahid101@gmail.com