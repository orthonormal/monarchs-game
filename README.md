## The Game of Monarchs
This repo encodes a three-way board game to be played within a unique social game.

# The Basic Idea
Monarchs is a game that combines a three-player board game with a social deception game and ideally with a themed party (similar in spirit to a murder mystery party). 

The players of the board game are the Monarchs of three nations. They are each confined to their own section of the party space - this is their court. The monarchs therefore rely on others to do their tasks, especially their five official courtiers. These courtiers are the only people at the party authorized to convey crucial hidden information between the monarch and the gamerunners.

However, two of those five courtiers are disloyal; there is one spy for each other court! The monarch is simultaneously trying to plan their moves, identify the traitors, and play the other monarchs against one another...

At the end, all will be revealed, one monarch will win, and separately three courtiers will win.

# The Board Game
A social game of deception goes well with something it's hard to do in regular board games: a fog of war. The game consists of fighting battles and winning territory with one's army regiments, but crucially, each monarch only ever sees what is happening in or adjacent to their territory.

Accordingly, this code is set up so that a gamerunner will take the orders from the three nations, simulate the battles and outcomes, and produce separate maps for the three nations - each displaying only the spaces within or adjacent to their territory.

Concretely, the game takes place on a hexagonal board with 61 total hexes. Here is the starting configuration:
![starting_hexes](https://user-images.githubusercontent.com/1791021/155652013-7c4971c0-b207-4aec-a336-f11fd74c7b05.png)

The color of the hex represents the nation it belongs to. The center hex starts out unclaimed. Each hex can host regiments of any color; these are tracked by the numbers in the middle of that hex. So hex A5 contains 3 red armies, for example.

There are two armies at most places along a nation's border, three armies where it borders the center, and three armies at the corner that serves as their home base. (More on this in a bit, but the home base is not a vulnerability to protect- it's an unconquerable hex where any defeated regiments will respawn.)

At the start of a turn, each monarch will receive (via a chosen courtier) the updated map, but it will only show the portion within or adjacent to their nation. For example, the red monarch might receive this:
![r_2](https://user-images.githubusercontent.com/1791021/155652220-8124a740-8797-4dc1-a12e-c16cafb102b6.png)

# Moving Regiments
The monarch will submit a batch of orders for moving regiments to adjacent hexes; in the above example, the blue monarch could submit the following list:
* 1 unit from D2 to C3
* 2 units from D2 to E3
* 2 units from M1 to L2
* 1 unit from F2 to E3

Note that this list contains an army splitting into separate groups (D2 sends 1 unit to C3 and the other 2 to E3) and two armies merging (M1 merges into L2). Think of them as interchangeable pieces on a board.

There is one other thing a monarch can (and should) include in their orders: they can choose to Bless one hex, and their armies will have an advantage should they happen to battle on that hex.

The Gamerunners will handle the data entry within the social game, but the actual input to the program must be of the following form:

    game.receive_orders(nation='g', order_dict={'Bless':'G9', ('G9','F8'):2, ('H8','F8'):1, ('H8','G7'):1})
    
# Battles and Retreats
Once the monarchs have submitted their orders, it is time to automatically resolve battles and update the game state.

There are two types of battles: border battles before the armies actually move onto new hexes, and then hex battles between armies occupying the same hex. 

The algorithm starts by checking for border battles. If two nations try to invade each other across the same border, they will fight a battle[^1]. The winner will move their armies onto the hex they were invading, and the loser will remain on that hex in order to defend.

After resolving the border battles and moving armies onto new hexes accordingly, the algorithm now fights hex battles to determine which army gets the hex. The other army/armies lose a regiment (which respawns immediately at home base) and are forced to retreat to a friendly[^2] adjacent hex. If a defeated army has no friendly hex to retreat to, then it is entirely lost and respawns at home base.

A battle (border or hex) is won by the army with the greatest strength. The strength is as follows:
The number of regiments
* + 0.25 if the army is fighting a hex battle on their own hex (defensive advantage)
* + 0.5 if it is a hex battle and the monarch Blessed the hex
* + a random number between 0 and 1

In essence, more armies almost always beat fewer armies, but tiebreakers matter for equal army sizes. Restricting to two-army situations, here are the stats:
* If neither army starts with any kind of advantage, then of course the chance of victory is 50% for each.
* An army that starts with 0.25 advantage (equal numbers plus defensive advantage, or alternately equal numbers minus defensive advantage but plus Bless) has a 72% chance of victory.
* It's rare to have a 0.5 advantage, but in that case it would have a 88% chance of victory.
* An army that has a 0.75 advantage (equal numbers plus defensive advantage plus Bless, or one more regiment minus defensive advantage) has a 97% chance of victory.
* An advantage of 1 or greater guarantees victory.

As mentioned before, we make an exception for the home bases, which can never be conquered.


[^1] Border battles are included because otherwise two armies could pass through each other without battling, and I don't think the resulting strategies would be as fun.
[^2] A hex is friendly if it started out with the nation and did not get conquered on that turn, or if the nation conquered the hex on that turn.
