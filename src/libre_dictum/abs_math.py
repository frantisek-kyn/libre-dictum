def abs_add(a, b):
    return (abs(a) + b) * (1 if a >= 0 else -1)

def abs_pow(a, b):
    return (abs(a) ** b) * (1 if a >= 0 else -1)

def abs_min(a, b):
    return min(abs(a), b) * (1 if a >= 0 else -1)
