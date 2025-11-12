<<<<<<< HEAD
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# NEW: Power function
def power(a, b):
    return a ** b

# NEW: Square root
def sqrt(a):
    if a < 0:
        raise ValueError("Cannot calculate square root of negative number")
=======
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# NEW: Power function
def power(a, b):
    return a ** b

# NEW: Square root
def sqrt(a):
    if a < 0:
        raise ValueError("Cannot calculate square root of negative number")
>>>>>>> 5f7bd0e (Organised the folder for PR Reviews and also implemented the Online Estimation Part. I have created a seperate file for Online Estimation For now just in case to compare the two versions. Later i will add the Online estimation part to version 1.2.1 and make the current as version 1.2.0)
    return a ** 0.5