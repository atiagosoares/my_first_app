
This is an app for playing the party game Who Am I?

The app is currently deployed on http://waionline.herokuapp.com/

# Who am I?

In Who Am I? players assign each other characaters (that may be real or fictional characters). Nobody knows which character they are. The game is played in turns. In each turn, players can ask single Yes or No question about who they are. The goal of the game is to guess which character you are.

On the pen and paper version, the name of the characters are written in paper cards (like post-it notes) and glued on the forehead of the players in a way the players can read the character's names on the other players foreheads, but not their on.

# App scope
The app replaces the need for pen and paper.

The game can be played by creating a room and joining the room by entering the room ID and room key. When all players are in the room, start the match.

On the character picking phase, every player will choose a character to another player, chosen at random. On the character guessing phase, every player can see a list with every other player and their characters, but not their own, plus a form for inputing character guesses.

The match ends (and returns to the lobby) when everyone guesses correctly or gives up, or if the host ends the match.

The game is meant to be played either in person or remotely via an audio or video call. The aspects of controlling turns, asking and aswering questions are meant to be controlled by the player outside the app. 

# Tech
Back end:
- Flask
- Socket io
- SQLlite

Front End:
- Vanilla JS
