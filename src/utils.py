from typing import Union

import httpx


http_client = httpx.AsyncClient(timeout=15)
http_client.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0"


def price_string_to_float(price_string: str) -> float:
    return float(price_string.replace("€", "").replace(" ", "").replace(",", ".").replace("-", "0"))


def int_to_roman(num: int) -> str:
    """
    Convert integers to roman numbers
    """
    ROMAN_DIGITS = [
        (1000, "M"), (900, "CM"), (500, "D"),
        (400, "CD"), (100, "C"), (90, "XC"),
        (50, "L"), (40, "XL"), (10, "X"),
        (9, "IX"), (5, "V"), (4, "IV"),
        (1, "I")
    ]

    roman = ""
    i = 0
    while num > 0:
        for _ in range(num // ROMAN_DIGITS[i][0]):
            roman += ROMAN_DIGITS[i][1]
            num -= ROMAN_DIGITS[i][0]
        i += 1
    return roman


def roman_to_int(roman: str) -> Union[int, None]:
    """
    Convert roman numbers to integers or return None if the input is invalid

    Examples:
    1. II -> 2
    2. VI -> 6
    3. XIX -> 19
    """
    ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

    if not roman:  # Empty string
        return

    total = 0
    prev_value = 0

    for char in roman:
        if char not in ROMAN_VALUES:  # Invalid character
            return

        current_value = ROMAN_VALUES[char]

        # If previous value is less, subtract it (for things like IV, IX)
        if current_value > prev_value:
            total += current_value - 2 * prev_value
        else:
            total += current_value

        prev_value = current_value

    # Validate that the final result
    if int_to_roman(total) != roman:
        return

    return total


def roman_string_to_int_string(string_with_roman: str) -> str:
    """
    Convert a string that includes roman numbers to one that only includes integers
    """
    name_list = []
    for word in string_with_roman.split(" "):
        int_word = roman_to_int(word)
        if int_word is None:
            name_list.append(word)
        else:
            name_list.append(str(int_word))
    return " ".join(name_list)
