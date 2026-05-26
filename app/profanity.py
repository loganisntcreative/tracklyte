BAD_WORDS = {
    'fuck', 'shit', 'ass', 'bitch', 'bastard', 'damn', 'crap',
    'piss', 'dick', 'cock', 'pussy', 'cunt', 'nigger', 'nigga',
    'faggot', 'fag', 'retard', 'whore', 'slut', 'asshole',
    'motherfucker', 'fucker', 'bullshit', 'jackass', 'dumbass',
    'dipshit', 'douchebag', 'douche', 'prick', 'twat', 'bollocks',
    'wanker', 'shithead', 'arsehole', 'arse', 'cuck', 'kike',
    'spic', 'chink', 'wetback', 'tranny', 'rape',
}

def contains_profanity(text):
    words = text.lower().split()
    for word in words:
        cleaned = ''.join(c for c in word if c.isalpha())
        if cleaned in BAD_WORDS:
            return True
    return False