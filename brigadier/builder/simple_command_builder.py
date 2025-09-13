import re

from typing import Optional, Callable, Any
from brigadier.arguments import string, integer, float_type, boolean
from brigadier.exceptions.command_syntax_exception import CommandSyntaxException
from brigadier.builder.required_argument_builder import argument
from brigadier.builder.literal_argument_builder import literal
from brigadier.tree.command_node import CommandNode

__command_value_regex = r"<(\w+)(?::(\w+))?>"  # 支持类型声明，如 <count:int>
__command_literal_regex = r"\w+"
__command_literal_pickone_regex = r"\((\w+(?:\|\w+)+)\)"
__command_literal_pickone_optional_regex = r"\[(\w+(?:\|\w+)+)\]"
__command_literal_optional = r"\[(\w+)\]"
__command_variadic = r"\.\.\."

# 类型映射表
TYPE_MAPPING = {
    "string": string,
    "str": string,
    "int": integer,
    "integer": integer,
    "float": float_type,
    "bool": boolean,
    "boolean": boolean,
}


def _parse_argument_type(arg_str: str) -> tuple[str, Any]:
    """解析参数名和类型"""
    match = re.match(__command_value_regex, arg_str)
    if not match:
        return "", None

    name = match.group(1)
    type_name = match.group(2) or "string"  # 默认为string类型
    return name, TYPE_MAPPING.get(type_name, string)


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


def _syntax_is_argument(_entry: str) -> bool:
    return re.match(__command_value_regex, _entry) is not None


class SimpleCommandBuilder:
    def __init__(self):
        self._command_root = None
        self._command_tree = None
        self._execute = None

    def command(self, command_str: str, execute=None):
        """命令注册装饰器或方法
        :param command_str: 命令语法字符串
        :param execute: 可选的执行函数
        """

        def decorator(func):
            self._setup(command_str, func)
            return func

        if execute is None:
            return decorator
        self._setup(command_str, execute)

    def _setup(self, command_str: str, execute: Callable):
        """设置命令配置"""
        command_parts = command_str.split()
        if not command_parts:
            raise CommandSyntaxException(ValueError, "Empty command string")

        if not _syntax_is_literal(command_parts[0]):
            raise CommandSyntaxException(
                TypeError, "The root command must be a literal node"
            )

        self._command_root = command_parts[0]
        self._execute = execute
        self._command_tree = self._parse_command_parts(command_parts[1:])

    def _parse_command_parts(self, parts: list[str]) -> Optional[CommandNode]:
        """
        递归解析命令字符串，返回命令节点链
        """
        if not parts:
            return None

        part = parts[0]
        rest = parts[1:]

        # 变长参数
        if _syntax_is_variadic(part):
            # 这里只做简单处理，实际可扩展
            node = argument("args", string)  # 默认类型为 string
            node.suggests(lambda ctx, builder: builder.suggest("..."))
            if rest:
                node.then(self._parse_command_parts(rest))
            return node

        # 必选分支
        pickone = _syntax_get_pickone_literals(part)
        if pickone:
            node = None
            for literal_name in pickone:
                child = literal(literal_name)
                if rest:
                    child.then(self._parse_command_parts(rest))
                if node is None:
                    node = child
                else:
                    node = node.or_(child)
            return node

        # 可选分支
        pickone_opt = _syntax_get_pickone_optional_literals(part)
        if pickone_opt:
            node = None
            for literal_name in pickone_opt:
                child = literal(literal_name)
                if rest:
                    child.then(self._parse_command_parts(rest))
                if node is None:
                    node = child
                else:
                    node = node.or_(child)
            # 可选分支，允许跳过
            if rest:
                node = node.or_(self._parse_command_parts(rest))
            return node

        # 可选单节点
        literal_opt = _syntax_get_literal_optional(part)
        if literal_opt:
            node = literal(literal_opt)
            if rest:
                node.then(self._parse_command_parts(rest))
            # 可选，允许跳过
            if rest:
                node = node.or_(self._parse_command_parts(rest))
            return node

        # 参数节点
        if _syntax_is_argument(part):
            name, arg_type = _parse_argument_type(part)
            if not name:
                raise CommandSyntaxException(
                    ValueError, f"Invalid argument format: {part}"
                )
            node = argument(name, arg_type)
            if not rest:
                node.executes(self._execute)
            else:
                node.then(self._parse_command_parts(rest))
            return node

        # 普通 literal
        if _syntax_is_literal(part):
            node = literal(part)
            if not rest:
                node.executes(self._execute)
            else:
                node.then(self._parse_command_parts(rest))
            return node

        raise CommandSyntaxException(TypeError, f"Unknown command part: {part}")

    def register(self, dispatcher):
        """注册命令到dispatcher"""
        if not self._command_root:
            raise CommandSyntaxException(ValueError, "No command registered")

        root = literal(self._command_root)
        if self._command_tree:
            root.then(self._command_tree)
        if self._execute:
            root.executes(self._execute)

        dispatcher.register(root)
