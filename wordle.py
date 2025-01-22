import math
import requests
from bs4 import BeautifulSoup
import re

def load_word_list(file_path):
    with open(file_path, 'r') as f:
        return [line.strip().upper() for line in f]

def get_todays_wordle():
    url = "https://www.tomsguide.com/news/what-is-todays-wordle-answer"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the paragraph containing the answer
    pattern = re.compile(r"it's ([A-Z]+)\.", re.IGNORECASE)
    for p in soup.find_all('p'):
        match = pattern.search(p.get_text())
        if match:
            return match.group(1).upper()
    
    raise ValueError("Could not find today's Wordle answer on the website")

def filter_words(guess, feedback, possible_words):
    constraints = {}
    for i, (letter, color) in enumerate(zip(guess, feedback)):
        if color == '🟩':
            constraints.setdefault(letter, {'min': 0, 'max': 5, 'positions': {}})
            constraints[letter]['positions'][i] = 'exact'
            constraints[letter]['min'] = max(constraints[letter].get('min', 0), 1)
        elif color == '🟨':
            constraints.setdefault(letter, {'min': 0, 'max': 5, 'positions': {}})
            constraints[letter]['positions'][i] = 'exclude'
            constraints[letter]['min'] = constraints[letter].get('min', 0) + 1
        elif color == '⬛':
            if letter not in constraints:
                constraints[letter] = {'min': 0, 'max': 0}
    
    filtered = []
    for word in possible_words:
        valid = True
        word_counts = {}
        for letter, rules in constraints.items():
            count = word.count(letter)
            if count < rules.get('min', 0) or count > rules.get('max', 5):
                valid = False
            for pos, rule in rules.get('positions', {}).items():
                if rule == 'exact' and word[pos] != letter:
                    valid = False
                elif rule == 'exclude' and word[pos] == letter:
                    valid = False
        if valid:
            filtered.append(word)
    return filtered

def letter_frequency_score(word, possible_words):
    freq = {}
    for w in possible_words:
        for i, c in enumerate(w):
            freq[(i, c)] = freq.get((i, c), 0) + 1
    return sum(freq.get((i, c), 0) for i, c in enumerate(word))

def entropy_score(word, possible_words):
    pattern_counts = {}
    for candidate in possible_words:
        feedback = simulate_feedback(word, candidate)
        pattern_counts[feedback] = pattern_counts.get(feedback, 0) + 1
    entropy = 0
    total = len(possible_words)
    for count in pattern_counts.values():
        if count == 0:
            continue
        p = count / total
        entropy -= p * math.log2(p)
    return entropy

def select_next_guess(possible_words, strategy='frequency'):
    if strategy == 'entropy':
        return max(possible_words, key=lambda w: entropy_score(w, possible_words))
    else:
        return max(possible_words, key=lambda w: letter_frequency_score(w, possible_words))

def simulate_feedback(guess, target):
    feedback = []
    guess_letters = list(guess)
    target_letters = list(target)
    
    # First pass: Check for green matches
    for i in range(5):
        if guess_letters[i] == target_letters[i]:
            feedback.append('🟩')
            guess_letters[i] = None
            target_letters[i] = None
        else:
            feedback.append('')
    
    # Second pass: Check for yellow matches
    for i in range(5):
        if feedback[i] == '' and guess_letters[i] in target_letters:
            feedback[i] = '🟨'
            target_letters.remove(guess_letters[i])
        elif feedback[i] == '':
            feedback[i] = '⬛'
    
    return tuple(feedback)

def solve_wordle(target_word, answer_list, allowed_guesses, strategy='frequency'):
    possible_words = answer_list.copy()
    guesses = []
    for _ in range(6):
        if not possible_words:
            break
            
        if not guesses:
            guess = 'CRANE'  # Optimal first guess
        else:
            guess = select_next_guess(possible_words, strategy)
            
        guesses.append(guess)
        feedback = simulate_feedback(guess, target_word)
        
        if feedback == ('🟩',)*5:
            return guesses
        
        possible_words = filter_words(guess, feedback, possible_words)
        
    return guesses

if __name__ == "__main__":
    # Load word lists (replace with actual file paths)
    answers = load_word_list('answers.txt')
    allowed = load_word_list('guesses.txt')
    
    # Get and solve today's Wordle
    try:
        target = get_todays_wordle()
        solution = solve_wordle(target, answers, allowed)
        print(f"Solved {target} in {len(solution)} guesses:")
        for idx, guess in enumerate(solution, 1):
            print(f"Guess {idx}: {guess}")
    except Exception as e:
        print(f"Error: {e}")