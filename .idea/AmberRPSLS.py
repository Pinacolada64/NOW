def rpssl(a, b):  # From http://samkass.com/theories/RPSSL.html
    choices = ('Spock', 'Scissors', 'Paper', 'Rock', 'Lizard')  # Order matters
    print("First player chooses " + choices[a] + '.')
    print("Second player chooses " + choices[b] + '.')
    n = len(choices)  # 3 choices in RPS, 5 in RPSLS
    difference = max(a, b) - min(a, b)
    # If difference is odd and A is smaller, A wins.
    first_wins = difference % 2 and a < b  # Who wins, by parity test
    winner = 0 if first_wins else 1  # Fist player is 0, Second is 1
    message = a * n  + b  # Enumerates combinations w/o itertools
    announce(winner, message)  # Announce the winner with appropriate message.

def announce(x, y):
    messages = ('Both players stalemate', 'Spock handles Scissors', 'Paper disproves Spock',
                'Spock blasts Rock', 'Lizard envenoms Spock',
                
                'Spock handles Scissors', 'Both players tie', 'Scissors cuts Paper',
                'Rock blunts Scissors', 'Scissors curtails Lizard',
                
                'Paper disproves Spock', 'Scissors cuts Paper', 'Both players draw',
                'Paper covers Rock', 'Lizard rips Paper',
                
                'Spock blasts Rock', 'Rock blunts Scissors', 
                'Paper covers Rock', 'Both players block', 'Rock buries Lizard',
                
                'Lizard envenoms Spock', 'Scissors curtails Lizard',
                'Lizard rips Paper', 'Rock buries Lizard', 'Both players standoff')
    print(messages[y] + '. ' + ('' if a == b else (('First', 'Second')[x] + ' player wins!')))
# --------------------TESTING BELOW -------------------
# xrange=5  # wot?
# So this is where we will create the Input
# for a in xrange(5): # Enumerates game choices for testing
#    for b in xrange(5):  # all possible game outcomes.
#        rpssl(a, b)
#        print('*-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-*')
playerchoices = ('Spock', 'Scissors', 'Paper', 'Rock', 'Lizard')
print ("Choose either")
print (repr(playerchoices))
playerspick = input("Choose: ")
print("This was your choice:",playerspick)
