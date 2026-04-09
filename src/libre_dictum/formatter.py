from itertools import product

DIGITS = [
    "zero", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine"
]

def expand_numeric_placeholders(strings):
    result = []

    for s in strings:
        count = s.count("{numeric}")

        # No placeholders, keep the string as-is
        if count == 0:
            result.append(s)
            continue

        # Generate every combination of digits for the placeholders
        for combo in product(DIGITS, repeat=count):
            expanded = s

            # Replace placeholders one at a time in order
            for digit in combo:
                expanded = expanded.replace("{numeric}", digit, 1)

            result.append(expanded)

    return result
