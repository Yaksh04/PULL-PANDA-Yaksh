<<<<<<< HEAD
def reverse_string(s):
    # BUG: This doesn't work for empty strings
    return s[::-1]

def count_vowels(s):
    # BUG: Counts 'y' as vowel incorrectly
    vowels = "aeiouy"
    return sum(1 for char in s.lower() if char in vowels)

def is_palindrome(s):
    # BUG: Doesn't handle case sensitivity
    return s == s[::-1]

def capitalize_words(s):
    # BUG: Multiple spaces cause issues
    words = s.split()
=======
def reverse_string(s):
    # BUG: This doesn't work for empty strings
    return s[::-1]

def count_vowels(s):
    # BUG: Counts 'y' as vowel incorrectly
    vowels = "aeiouy"
    return sum(1 for char in s.lower() if char in vowels)

def is_palindrome(s):
    # BUG: Doesn't handle case sensitivity
    return s == s[::-1]

def capitalize_words(s):
    # BUG: Multiple spaces cause issues
    words = s.split()
>>>>>>> 5f7bd0e (Organised the folder for PR Reviews and also implemented the Online Estimation Part. I have created a seperate file for Online Estimation For now just in case to compare the two versions. Later i will add the Online estimation part to version 1.2.1 and make the current as version 1.2.0)
    return ' '.join(word.capitalize() for word in words)