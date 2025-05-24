from typing import Any, cast

import esprima
import httpx

http_client = httpx.AsyncClient(timeout=15)
http_client.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0"
http_client.headers["Accept-Language"] = "en-US,en;q=0.5"


_ROMAN_DIGITS = [
    (1000, "M"), (900, "CM"), (500, "D"),
    (400, "CD"), (100, "C"), (90, "XC"),
    (50, "L"), (40, "XL"), (10, "X"),
    (9, "IX"), (5, "V"), (4, "IV"),
    (1, "I")
]

_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


class ANSICodes:
    """ANSI color and style codes."""

    RESET = "\033[0m"

    BOLD = "\033[1m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"


def price_string_to_float(price_string: str) -> float:
    """Convert a price string to a float."""
    return float(price_string.replace("€", "").replace(" ", "").replace(",", ".").replace("-", "0"))


def int_to_roman(num: int) -> str:
    """Convert integers to roman numbers."""
    roman = ""
    i = 0
    while num > 0:
        for _ in range(num // _ROMAN_DIGITS[i][0]):
            roman += _ROMAN_DIGITS[i][1]
            num -= _ROMAN_DIGITS[i][0]
        i += 1
    return roman


def roman_to_int(roman: str) -> int | None:
    """
    Convert roman numbers to integers or return None if the input is invalid.

    Examples:
    1. II -> 2
    2. VI -> 6
    3. XIX -> 19

    """
    if not roman:  # Empty string
        return

    total = 0
    prev_value = 0

    for char in roman:
        if char not in _ROMAN_VALUES:  # Invalid character
            return

        current_value = _ROMAN_VALUES[char]

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
    """Convert a string that includes roman numbers to one that only includes integers."""
    name_list = []
    for word in string_with_roman.split(" "):
        int_word = roman_to_int(word)
        if int_word is None:
            name_list.append(word)
        else:
            name_list.append(str(int_word))
    return " ".join(name_list)


def read_js_variables(script_content: str) -> dict[str, Any]:
    """Read JavaScript variables from a string."""

    def read_obj(obj):
        if obj.type == "Identifier":
            return obj.name
        elif obj.type == "MemberExpression":
            end = obj.property.name
            start = read_obj(obj.object)
            if start is not None:
                return f"{start}.{end}"
        elif obj.type == "Literal":
            return obj.value
        elif obj.type == "ArrayExpression":
            return [read_obj(element) for element in obj.elements]
        elif obj.type == "ObjectExpression":
            return {read_obj(property.key): read_obj(property.value) for property in obj.properties}

    ast = esprima.parseScript(script_content)
    vars: dict[str, Any] = {}
    for node in ast.body:
        if node.type == "VariableDeclaration":
            for decl in node.declarations:
                vars[decl.id.name] = read_obj(decl.init)
        elif all((
            node.type == "ExpressionStatement",
            node.expression.type == "AssignmentExpression",
            node.expression.operator == "="
        )):
            name = cast(str, read_obj(node.expression.left))
            if name is not None:
                vars[name] = read_obj(node.expression.right)
    return vars
