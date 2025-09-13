import re

__command_value_regex = r"<\w+>"
__command_literal_regex = r"\w+"
__command_literal_pickone_regex = r"\((\w+\|)+\w+\)"
__command_literal_pickone_optional_regex = r"\[(\w+\|)+\w+\]"
__command_literal_optional = r"\[\w+\]"
__command_variadic = r"\.\.\."


def _syntax_get_value(_value: str) -> str:
    match = re.match(__command_value_regex, _value)
    if match:
        return match.group(0)[1:-1]
    return ""


def _syntax_is_literal(_literal: str) -> bool:
    return re.match(__command_literal_regex, _literal) is not None


def _syntax_get_pickone_literals(_entries: str) -> list[str]:
    match = re.match(__command_literal_pickone_regex, _entries)
    if match:
        inner = _entries[1:-1]
        return inner.split("|")
    return []


def _syntax_get_pickone_optional_literals(_entries: str) -> list[str]:
    match = re.match(__command_literal_pickone_optional_regex, _entries)
    if match:
        inner = _entries[1:-1]
        return inner.split("|")
    return []


def _syntax_get_literal_optional(_entry: str) -> str:
    match = re.match(__command_literal_optional, _entry)
    if match:
        return _entry[1:-1]
    return ""


def _syntax_is_variadic(_entry: str) -> bool:
    return re.match(__command_variadic, _entry) is not None


class SimpleCommandBuilder:
    def __init__(self):
        pass

    def command(self, command_str: str):
        ## Brigadier Syntax:
        # - Directly as literal nodes.
        # e.g.
        # command entry
        # - Typed as argument values.
        # e.g.
        # command <entry>
        # - Required nodes and need to pick one.
        # e.g.
        # command (entry|entry)
        # - Optional nodes and can pick one or not.
        # e.g.
        # command [entry|entry]
        # - Extra contents need to be parsed in further stages.
        # e.g.
        # command ...
        command_parts = command_str.split()
