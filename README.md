# The Game of Monarchs
This repo encodes a three-way board game intended to be played within a unique social game.

## The Basic Idea
Monarchs is a game that combines a three-player board game with a social deception game and ideally with a themed party (similar in spirit to a murder mystery party). 

The players of the board game are the Monarchs of three nations. They are each confined to their own section of the party space - this is their court. The monarchs therefore rely on others to do their tasks, especially their five official courtiers. These courtiers are the only people at the party authorized to convey crucial hidden information between the monarch and the gamerunners.

However, two of those five courtiers are disloyal; there is one spy for each other court! The monarch is simultaneously trying to plan their moves, identify the traitors, and play the other monarchs against one another...

At the end, all will be revealed, one monarch will win, and separately three courtiers will win.

# The Board Game
A social game of deception goes well with something it's hard to do in regular board games: a fog of war. The game consists of fighting battles and winning territory with one's army regiments, but crucially, each monarch only ever sees what is happening in or adjacent to their territory.

Accordingly, this code is set up so that a gamerunner will take the orders from the three nations, simulate the battles and outcomes, and produce separate maps for the three nations - each displaying only the spaces within or adjacent to their territory.

# The Board
Concretely, the game takes place on a hexagonal board with 61 total hexes. Here is the starting configuration:![start_map](https://user-images.githubusercontent.com/1791021/161457783-e69b661a-1e89-4207-bc0d-ad0011f9de44.png)

The color of the hex represents the nation it belongs to. The center hex starts out unclaimed. Each hex can host regiments of any color; these are tracked by the numbers in the middle of that hex. So hex H6 contains 3 red armies, for example.

There are two armies at most places along a nation's border, three armies where it borders the center, and five armies at the corner that serves as their home base. (More on this in a bit, but the home base is not a vulnerability to protect- it's an unconquerable hex where any defeated regiments will respawn.)

At the start of a turn, each monarch will receive (via a chosen courtier) the updated map, but it will only show the portion within or adjacent to their nation. For example, the red monarch might receive this:

![r_2](https://user-images.githubusercontent.com/1791021/161459350-97478b6d-4875-419b-b5ce-919d48630cf1.png)

## Moving Regiments
The monarch will submit a batch of orders for moving regiments to adjacent hexes; in the above example, the red monarch could submit the following list:
* 5 units from C5 to D4
* 1 unit from F2 to H2
* 1 unit from F2 to G1
* 1 unit from E7 to G7

Note that this list contains an army splitting into separate groups (F2 sends 1 unit to H2 and the other 1 to G1) and two armies merging (E7 merges its unit with the units on G7). Think of them as interchangeable pieces on a board.

There is one other thing a monarch can (and should) include in their orders: they can choose to Boost one hex, and their armies will have an advantage should they happen to battle on that hex.

The Gamerunners will handle the data entry within the social game, but the actual input to the program will be of the following form:

    game.receive_orders(nation='g', order_dict={'boost':'G9', ('G9','F8'):2, ('H8','F8'):1, ('H8','G7'):1})
    
## Battles and Retreats
Once the monarchs have submitted their orders, it is time to automatically resolve battles and update the game state.

There are two types of battles: border battles before the armies actually move onto new hexes, and then hex battles between armies occupying the same hex. 

The algorithm starts by checking for border battles. If two nations try to invade each other across the same border, they will fight a battle[^1]. The winner will move their armies onto the hex they were invading, and the loser will remain on that hex in order to defend.

After resolving the border battles and moving armies onto new hexes accordingly, the algorithm now fights hex battles to determine which army gets the hex. The other army/armies lose a regiment (which respawns immediately at home base) and are forced to retreat to a friendly[^2] adjacent hex. If a defeated army has no friendly hex to retreat to, then it is entirely lost and respawns at home base.

A battle (border or hex) is won by the army with the greatest strength. The strength is as follows:
The number of regiments (if nonzero)
* plus 0.25 if the army is fighting a hex battle on their own hex (defensive advantage)
* plus 0.5 if it is a hex battle and the monarch boosted the hex
* plus a random number between 0 and 1

In essence, more armies almost always beat fewer armies, but the modifiers matter if the army sizes differ by 0 or 1. Restricting to two-army situations, here are the stats:
* If neither army starts with any kind of advantage, then of course the chance of victory is 50% for each.
* An army that starts with 0.25 advantage (e.g. equal numbers plus defensive advantage, or equal numbers minus defensive advantage but plus a boost) has a 72% chance of victory.
* It's rare to have a 0.5 advantage, but in that case it would have a 88% chance of victory.
* An army that has a 0.75 advantage (e.g. equal numbers plus defensive advantage plus a boost, or one more regiment minus defensive advantage) has a 97% chance of victory.
* An advantage of 1 or greater guarantees victory.

As mentioned before, we make an exception for the home bases, which can never be conquered.

## Battle Example
We will give an example that illustrates some subtle points. On the starting board (not the second example), consider the following moves:
* Red boosts F2.
* Red moves 2 regiments from D2 to E3.
* Red moves 2 regiments from E3 to F2.
* Blue boosts E3.
* Blue moves 1 regiment from F2 to E3.
* Blue moves 2 regiments from G3 to E3.
* Blue moves 1 regiment from E1 to F2.
* Blue moves 1 regiment from E1 to D2.

The only border battle is on the boundary between E3 and F2, because opposing armies are both moving across the same border. There is no border battle for different nations entering the same hex through _different_ borders; so the armies entering E3 from D2 and from G3 do not cause a border battle.

Since a border battle has no boosts and no defensive advantage, 2 armies always beat 1 even with the random number added. So all the moves above happen except for the move from F2 to E3.

After those moves, we have the following combinations of armies:![example](https://user-images.githubusercontent.com/1791021/161463092-b85b15d6-33a1-4fee-aba6-3c76d004d7d2.png)

* 1 Blue regiment on the previously Red hex D2. (This becomes Blue without a battle.)
* 2 Red regiments and 3 Blue regiments on the previously Blue hex F2, boosted by Red.
* 2 Red regiments and 2 Blue regiments on the previously Red hex E3, boosted by Blue.

On F2, Red has a strength of 2 regiments + 0.5 boost, while Blue has a strength of 3 regiments + 0.25 defensive advantage. This gives Blue a 97% chance of victory.

On E3, Red has a strength of 2 regiments + 0.25 defensive advantage, while Blue has a strength of 2 regiments + 0.5 boost. This gives Blue a 72% chance of victory.

Let's consider two of the four possibilities. If Blue wins on F2 but Red wins on E3, then Red loses a unit on F2 and the other unit retreats to its only available Red neighbor E3, and similarly Blue loses a unit on E3 and the other unit retreats (randomly) to either G3 or F2.

However, if Blue wins on both hexes, then Red loses a unit on E3, while its other unit retreats to either C3 or D4 - but not to F4 because that is farther from Red's home base. Red loses a unit on F2, but its other unit there is fully surrounded and therefore is defeated as well.

All defeated units respawn at the home base, of course.

## Scoring

Every turn, a nation's score is increased by the number of hexes it controls, plus twice the number of regiments it defeated, minus twice the number of regiments it lost. The contribution of the last turn is doubled.

Note the following:
* It doesn't only matter how the board looks at the end; winning battles and holding hexes earlier in the game is just as essential for victory.
* The scoring counts _regiments defeated_ rather than _battles won_, so that surrounding and totally defeating an enemy army counts for more than just one victory.
* The total number of points every round is 61 (notwithstanding the last round being doubled), so the average score is 20 1/3.

# The Social Game
The board game would be fun in isolation, I hope, but it should be much more interesting as the matrix for a game of social deception and deduction, similar to The Resistance.

## Monarchs and Courtiers
The three players of the game are the Monarchs of three nations. They each reside in their own court, isolated enough to prevent easy eavesdropping from outside the court. The party venue spans these three courts as well as a common area connecting them.

A Monarch may not leave their court for any purpose[^3]. Even non-game party activities should be achieved the way a true monarch would: by asking a courtier to fetch a drink or summon a person, etc.

Each Monarch has five Courtiers. Three of them are fully loyal, and then there is one loyal to each other Monarch - though they are strongly incentivized not to get caught as traitors.

The main role of the Courtiers is to deliver signed orders to the Gamerunners, and then pick up the new maps. However, the Courtiers can modify the orders[^4], and can read / take notes on the maps. This potential for malfeasance is at the heart of the social game.

(The Gamerunners must enforce plausible deniability by making even honest Courtiers take 60 seconds of waiting, while visible to nobody except for the Gamerunners, on order delivery and on map reception.)

Since it would be too easy to choose only one or two Courtiers to trust, a Monarch is not allowed to use a Courtier who either delivered their most recent orders _or_ who received their most recent map.

Each round, from the moment that the Courtiers with the new maps are released until the deadline for the Courtiers to arrive with the new orders, is 15 minutes. If new orders are not ready by then, it is treated as if no orders were given (no units move, no hex is boosted). Each court should be provided with a timer so that nobody has to use their phone.

Monarchs have the power to dismiss someone from their Court, either temporarily or permanently. They also have the ability to summon one person at a time to their court, if that person is in the comon area of the party. (It might be useful to have the summons represented in a physical object.) No player can refuse a dismissal or a summons, with the exception that delivering orders and receiving maps take precedence over being summoned. A summoned person has to remain in that court for at least one minute.

Finally, in order to prevent the strategy of keeping everyone in the court so that nobody can convey information to other Monarchs, only three of a nation's Courtiers can be in their court simultaneously.

## Winning Monarch, Winning Courtiers
The game ends with the round that passes the three-hour mark. (Depending on how fast this is to run / how many bugs there are, this is probably around eight turns.)

At the end of the final round (after the last orders have been submitted, but without any outcomes shown), a Gamerunner comes directly to each Monarch and asks them to guess the identity of the two traitors, as well as which other Monarch they each serve.

There will be one winning Monarch and three winning Courtiers.

The victory conditions begin with the nations' total scores, as defined above (1 point per hex controlled per turn, plus 2 points for every enemy regiment defeated, minus 2 points for every regiment lost, and the final turn counts double).

Each Monarch's score is their nation's score at game end, plus five points per traitor _if they correctly identified that traitor's true nation_. The highest Monarch score wins; the first tiebreaker is which of them controls the middle; the second tiebreaker is the number of hexes controlled at game end; otherwise flip a coin (if there is a non-splittable prize).

For Courtiers, one courtier with the highest score (or tied for it) is a winner; but two other courtiers win as well, and those winners are chosen by a raffle. If a Courtier has a score of X, they get X^2 raffle tickets[^5]. This rewards the top scorers best, but makes it worthwhile to get even a moderately positive score.

A loyal Courtier's score is their Monarch's score, minus a constant[^6].

A disloyal Courtier's score is twice the score of the Monarch they truly serve, minus the score of the Monarch they pretend to serve, minus a different constant. (They not only want their true nation to win, they want their feigned nation to fail.)

*Any Courtier (loyal or disloyal!) whose Monarch calls them disloyal at the end of the game has their score divided by two (rounded down).*

## Advice to Players
Even though this advice is directed at individual roles, I recommend you glance through advice for the other roles, so that you'll know what you might expect from them.
### Monarchs
* SUBMIT YOUR ORDERS ON TIME. Write a draft version of your orders early on. You can always edit it during the turn. But you don't want to wind up with 30 seconds left and nothing written down.
* DOUBLE-CHECK YOUR ORDERS. Illegal moves will be ignored by the program (alerting the Gamerunners but not stopping the turn). Don't try and send more regiments out from a hex than are on it, don't try and move a regiment to a non-adjacent hex, don't use a name which doesn't correspond to a hex (e.g. F5), etc.
* Keep notes of your past orders. Try and carefully assess whether the outcome is a possible result of the orders you sent in. If not, you may be dealing with a traitor.
* It's worth trying to negotiate with the other monarchs; a 2 vs 1 pile-on can rack up the points, and if you're lucky you can get both fighting each other while you betray them! Just think carefully about who you send- you don't want to give a traitor an excuse to talk to their liege.
* Keep in mind your unrestricted power of dismissal. You don't need to let a traitor stick around if you've figured them out.
* Your power to summon courtiers from other courts lets you keep in contact with your agents; but in order to protect them from suspicion, you might want to also regularly summon courtiers you know are loyal to their Monarchs, even if they have nothing to say to you.

### Traitors
* Skipping the "boost" order, for a hex that the nation is invading at equal numbers, will swing the odds from 72% to 28%, which makes it a plausibly deniable method of sabotage.
* Your single most valuable opportunity is being chosen to deliver the orders in the final round, because the monarch will not know the outcome until after they have made their guesses about loyalty, which allows you to commit massive sabotage without repercussion.
  * An effective strategy in that situation is to retreat the larger armies, creating a frontier of hexes that opponents can conquer entirely for free or (even better) by defeating a single regiment.
  * If your cumulative score is low, this can even be worth doing on an earlier turn! Having a good score cut in half is preferable to having a bad score.
* Remember that you have a counterspy, someone in your true nation's court who works for your perceived nation. Try to figure out who they are and rat them out to your true monarch, so that your true monarch can avoid giving you away to them.

(Honest Courtiers have relatively simple incentives to support the Monarch, ferret out the traitors, and avoid coming under false suspicion, so they don't need a section here.)

# Considerations for Gamerunners
* Find a venue with a common area connecting four adequately sound-isolated spaces (one for each court and one for the Gamerunners).
* Practice the game. I've got the game-running phase down to under 10 minutes per turn.
* Have a printer as well as a backup. (Maybe a separate printer, maybe simply pre-printed hex grids and colored markers.)
* Arrange your players in advance; it's important to make sure the Monarchs and Courtiers are excited about their roles and can study them in advance.
  * Designate an understudy Monarch in case one of them cannot attend; similarly, have at least one understudy Courtier.
  * The Courtiers should not know until the night of the game where their loyalty lies.
* You can give the game a running start by asking the Monarchs to _directly_ submit their first orders before the party, perhaps before they know who else is playing what role. Their first move would therefore be purely based on the board game.
* Helpful physical objects:
  * Unmistakable insignia for the courtiers of each nation (e.g. a brooch, a temporary tattoo, a required color scheme for clothing)
  * Timers for the courts
  * Tokens to represent a summons
* Works with party themes including medieval, fantasy, science fiction, etc

# Footnotes

[^1] Border battles are included because otherwise two armies could pass through each other without battling, and I don't think the resulting strategies would be as fun.

[^2] A hex is friendly if it started out with the nation and did not get conquered on that turn, or if the nation conquered the hex on that turn.

[^3] Except for the bathroom and for emergencies and any other common-sense exceptions.

[^4] That is, a Courtier can change the content of a set of orders entrusted to them by their Monarch. A Courtier cannot falsely claim to be the deliverer of orders.

[^5] Negative scores count as zero raffle tickets.

[^6] My current best guess of how to properly balance the game: For loyal Courtiers, the constant is eighteen times (the number of rounds plus one); the plus one is to account for double-scoring the last round. For disloyal Courtiers, the constant is nineteen times (the number of rounds plus one).
