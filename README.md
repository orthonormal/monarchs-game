# The Game of Monarchs
This repo encodes a three-way board game to be played within a unique social game.

## The Basic Idea
Monarchs is a game that combines a three-player board game with a social deception game and ideally with a themed party (similar in spirit to a murder mystery party). 

The players of the board game are the Monarchs of three nations. They are each confined to their own section of the party space - this is their court. The monarchs therefore rely on others to do their tasks, especially their five official courtiers. These courtiers are the only people at the party authorized to convey crucial hidden information between the monarch and the gamerunners.

However, two of those five courtiers are disloyal; there is one spy for each other court! The monarch is simultaneously trying to plan their moves, identify the traitors, and play the other monarchs against one another...

At the end, all will be revealed, one monarch will win, and separately three courtiers will win.

# The Board Game
A social game of deception goes well with something it's hard to do in regular board games: a fog of war. The game consists of fighting battles and winning territory with one's army regiments, but crucially, each monarch only ever sees what is happening in or adjacent to their territory.

Accordingly, this code is set up so that a gamerunner will take the orders from the three nations, simulate the battles and outcomes, and produce separate maps for the three nations - each displaying only the spaces within or adjacent to their territory.

# The Board
Concretely, the game takes place on a hexagonal board with 61 total hexes. Here is the starting configuration:
![starting_hexes](https://user-images.githubusercontent.com/1791021/155652013-7c4971c0-b207-4aec-a336-f11fd74c7b05.png)

The color of the hex represents the nation it belongs to. The center hex starts out unclaimed. Each hex can host regiments of any color; these are tracked by the numbers in the middle of that hex. So hex A5 contains 3 red armies, for example.

There are two armies at most places along a nation's border, three armies where it borders the center, and three armies at the corner that serves as their home base. (More on this in a bit, but the home base is not a vulnerability to protect- it's an unconquerable hex where any defeated regiments will respawn.)

At the start of a turn, each monarch will receive (via a chosen courtier) the updated map, but it will only show the portion within or adjacent to their nation. For example, the red monarch might receive this:
![r_2](https://user-images.githubusercontent.com/1791021/155652220-8124a740-8797-4dc1-a12e-c16cafb102b6.png)

## Moving Regiments
The monarch will submit a batch of orders for moving regiments to adjacent hexes; in the above example, the blue monarch could submit the following list:
* 1 unit from D2 to C3
* 2 units from D2 to E3
* 2 units from M1 to L2
* 1 unit from F2 to E3

Note that this list contains an army splitting into separate groups (D2 sends 1 unit to C3 and the other 2 to E3) and two armies merging (M1 merges into L2). Think of them as interchangeable pieces on a board.

There is one other thing a monarch can (and should) include in their orders: they can choose to Bless one hex, and their armies will have an advantage should they happen to battle on that hex.

The Gamerunners will handle the data entry within the social game, but the actual input to the program must be of the following form:

    game.receive_orders(nation='g', order_dict={'Bless':'G9', ('G9','F8'):2, ('H8','F8'):1, ('H8','G7'):1})
    
## Battles and Retreats
Once the monarchs have submitted their orders, it is time to automatically resolve battles and update the game state.

There are two types of battles: border battles before the armies actually move onto new hexes, and then hex battles between armies occupying the same hex. 

The algorithm starts by checking for border battles. If two nations try to invade each other across the same border, they will fight a battle[^1]. The winner will move their armies onto the hex they were invading, and the loser will remain on that hex in order to defend.

After resolving the border battles and moving armies onto new hexes accordingly, the algorithm now fights hex battles to determine which army gets the hex. The other army/armies lose a regiment (which respawns immediately at home base) and are forced to retreat to a friendly[^2] adjacent hex. If a defeated army has no friendly hex to retreat to, then it is entirely lost and respawns at home base.

A battle (border or hex) is won by the army with the greatest strength. The strength is as follows:
The number of regiments (if nonzero)
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

## Examples
On the board above, consider the following moves:
* Red moves 1 regiment from I9 to H8. (One can merge armies.)
* Green moves 2 regiments from G7 to H8.
* Red moves 1 regiment from F2 to E1, and 1 regiment from F2 to G1. (One can split armies.)
* Blue moves 3 regiments from E3 to F2.
* Red moves 2 armies from G5 to H6.
* Green moves 2 armies from H6 to G5.
* Blue moves 3 armies from H4 to G5.

The final pair of movements will trigger a border battle; none of the previous ones will, since none of them use the same pair of hexes in reverse.

There will be a battle on H8, with two red regiments (on a red hex) against two green regiments. This gives the 72% advantage to the red regiments.

The unoccupied hexes E1, G1, and (once the moves are complete) F2 will change hands without battles.

The border battle between G5 and H6 is 50-50, but the winner of the battle will unfortunately face longer odds in the hex battle, as they will push into defensive advantage and (if Green wins) an extra regiment waiting for them.

Moreover, if Red wins the border battle, their one remaining regiment on G5 will lose to the Blue army there; but if Red loses the border battle, it will have the best chance of beating both Green and Blue on G5.

# The Social Game
The board game would be fun in isolation, I hope, but it may be much more interesting as the matrix for a game of social deception and deduction, similar to The Resistance.

## Monarchs and Courtiers
The three players of the game are the Monarchs of three nations. They each reside in their own court, isolated enough to prevent easy eavesdropping from outside the court. The party venue spans these three courts as well as a common area connecting them.

A Monarch may not leave their court for any purpose[^3]. Even non-game party activities should be achieved the way a true monarch would: by asking a courtier to fetch a drink or summon a person, etc.

A Monarch can exile any person from their court, for any reason, and that person must comply immediately.

Each Monarch has five Courtiers. Three of them are fully loyal, and then there is one loyal to each other Monarch - though they are strongly incentivized not to get caught as traitors.

The main role of the Courtiers is to deliver signed orders to the Gamerunners, and then pick up the new maps. However, the Courtiers can modify the orders[^4], and can read / take notes on the maps. This potential for malfeasance is at the heart of the social game.

(The Gamerunners must enforce plausible deniability by making even honest Courtiers take 60 seconds of waiting, while visible to nobody except for the Gamerunners, on order delivery and on map reception.)

Since it would be too easy to just find a single trusted Courtier, a Monarch is not allowed to use a Courtier who either delivered their most recent orders or who received their most recent map. They must cycle through at least three.

Each round, from the moment that the Courtiers with the new maps are released until the deadline for the Courtiers to arrive with the new orders, is 15 minutes. If new orders are not ready by then, it is treated as if no orders were given (no units move, no hex is Blessed). Each court should be provided with a timer so that nobody has to use their phone.

## Winning Monarch, Winning Courtiers
The game ends with the round that passes the three-hour mark. (Depending on how fast this is to run / how many bugs there are, this is probably around eight turns.)

At the end of the final round (after the last orders have been submitted, but without any outcomes shown), a Gamerunner comes directly to each Monarch and asks them to guess the identity of the two traitors, as well as which other Monarch they each serve.

There will be one winning Monarch and three winning Courtiers.

The victory conditions are in terms of the nations' total scores.

Every turn, a nation's score is increased by the number of hexes it controls, plus the number of battles it won, minus the number of battles it lost. (It doesn't only matter how the board looks at the end; owning more hexes earlier in the game gives you points as well!) The contribution of the last turn is doubled.

Each Monarch's score is their nation's score at game end, plus five points per traitor if they correctly identified that traitor's true loyalty. The highest Monarch score wins; the first tiebreaker is which of them controls the middle; the second tiebreaker is the number of hexes controlled; otherwise flip a coin (if there is a non-splittable prize).

For Courtiers, the highest score does not necessarily win. Every point is a raffle ticket[^5], and at the end, three distinct winners will be chosen with those tickets.

A loyal Courtier's score is their nation's score, minus a constant[^6].

A disloyal Courtier's score is twice the score of the nation they truly serve, minus the score of the nation they pretend to serve, minus a different constant. (They not only want their true nation to win, they want their feigned nation to fail.)

Any Courtier (loyal or disloyal!) whose Monarch calls them disloyal at the end of the game forfeits half of their points (rounded down).

## Advice to Players
Even though this advice is directed at individual roles, I recommend you glance through advice for the other roles, so that you'll know what you might expect from them.
### Monarchs
* SUBMIT YOUR ORDERS ON TIME. Write a draft version of your orders early on. You can always edit it during the turn. But you don't want to wind up with 30 seconds left and nothing written down.
* DOUBLE-CHECK YOUR ORDERS. Illegal moves will silently be thrown out by the program. Don't try and send more regiments out from a hex than are on it, don't try and move a regiment to a non-adjacent hex, don't use a name which doesn't correspond to a hex (e.g. F5), etc.
* Keep notes of your past orders. Try and carefully assess whether the outcome is a possible result of the orders you sent in. If not, you may be dealing with a traitor.
* It's worth trying to negotiate with the other monarchs; a 2 vs 1 pile-on can rack up the points, and if you're lucky you can get both fighting each other while you betray them! Just think carefully about who you send- you don't want to give a traitor an excuse to talk to their liege.
* Keep in mind your unrestricted power of banishment. You don't need to let a traitor stick around if you've figured them out.

### Traitors
* Skipping the "Bless" order, for a hex that the nation is invading at equal numbers, will swing the odds from 77% to 23%, which makes it a plausibly deniable method of sabotage.
* Your single most valuable opportunity is being chosen to deliver the orders in the final round, because the monarch will not know the outcome until after they have made their guesses about loyalty, which allows you to commit massive sabotage without repercussion.
  * An effective strategy in that situation is to retreat the larger armies, creating a frontier of hexes that opponents can conquer entirely for free or (even better) by defeating a single regiment.
  * If your cumulative score is low enough, this can even be worth doing on the second-to-last turn! Having a decent score cut in half can be preferable to having a very low score.
* Remember that you have a counterspy, someone in your true nation's court who works for your perceived nation. Try to figure out who they are and rat them out to your true monarch, so that your true monarch can avoid giving you away to them.

(Honest Courtiers have relatively simple incentives to support the nation and avoid coming under false suspicion, so they don't need a section here.)



[^1] Border battles are included because otherwise two armies could pass through each other without battling, and I don't think the resulting strategies would be as fun.

[^2] A hex is friendly if it started out with the nation and did not get conquered on that turn, or if the nation conquered the hex on that turn.

[^3] Except for the bathroom and for emergencies and any other common-sense exceptions.

[^4] That is, a Courtier can change the content of a set of orders entrusted to them by their Monarch. A Courtier cannot falsely claim to be the deliverer of orders.

[^5] Negative scores count as zero raffle tickets.

[^6] My current best guess of how to properly balance the game: For loyal Courtiers, the constant is eighteen times (the number of rounds plus one); the plus one is to account for double-scoring the last round. For disloyal Courtiers, the constant is nineteen times (the number of rounds plus one).
