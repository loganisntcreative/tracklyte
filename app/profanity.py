import re

BAD_WORDS = {
    'fuck', 'shit', 'ass', 'bitch', 'bastard', 'crap',
    'piss', 'dick', 'cock', 'pussy', 'cunt', 'nigger', 'nigga',
    'faggot', 'fag', 'retard', 'whore', 'slut', 'asshole',
    'motherfucker', 'fucker', 'bullshit', 'jackass', 'dumbass',
    'dipshit', 'douchebag', 'douche', 'prick', 'twat', 'bollocks',
    'wanker', 'shithead', 'arsehole', 'arse', 'cuck', 'kike',
    'spic', 'chink', 'wetback', 'tranny', 'rape',
}

BORDERLINE_WORDS = {
    'damn', 'hell', 'crap', 'sucks', 'stupid', 'idiot',
    'dumb', 'loser', 'moron', 'jerk', 'freak', 'ugly',
    'hate', 'pathetic', 'worthless', 'trash', 'garbage',
}

LEET_MAP = {
    '0': 'o', '1': 'i', '2': 'z', '3': 'e', '4': 'a',
    '5': 's', '6': 'g', '7': 't', '8': 'b', '9': 'g',
    '@': 'a', '$': 's', '!': 'i', '+': 't', '*': '',
}


def normalize(text):
    text = text.lower()
    result = ''
    for ch in text:
        result += LEET_MAP.get(ch, ch)
    result = re.sub(r'(.)\1{2,}', r'\1\1', result)
    result = re.sub(r'[^a-z\s]', '', result)
    return result


def _get_words(text):
    normalized = normalize(text)
    return set(normalized.split())


def contains_profanity(text):
    words = _get_words(text)
    for word in words:
        if word in BAD_WORDS:
            return True
        for bad in BAD_WORDS:
            if bad in word and len(bad) >= 4:
                return True
    return False


def contains_borderline(text):
    words = _get_words(text)
    for word in words:
        if word in BORDERLINE_WORDS:
            return True
    return False