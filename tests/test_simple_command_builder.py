from brigadier.builder.simple_command_builder import (
    _syntax_get_value,
    _syntax_is_literal,
    _syntax_get_pickone_literals,
)


def test_syntax_get_value():
    _test = _syntax_get_value("<value>")
    print(_test)
    assert _test == "value"


def test_syntax_is_literal():
    assert _syntax_is_literal("value")
    assert not _syntax_is_literal("<value>")
    assert not _syntax_is_literal("(value|value)")
    assert not _syntax_is_literal("[value|value]")
    assert not _syntax_is_literal("[value]")
    assert not _syntax_is_literal("...")


def test_syntax_get_pickone_literals():
    _test = _syntax_get_pickone_literals("(entry1|entry2|entry3)")
    assert _test == ["entry1", "entry2", "entry3"]
