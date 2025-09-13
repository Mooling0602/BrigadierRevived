from brigadier import CommandDispatcher
from brigadier.builder import SimpleCommandBuilder
from brigadier.context.command_context import CommandContext

simple_builder = SimpleCommandBuilder()
dispatcher = CommandDispatcher()


@simple_builder.command("echo <name>")
def hello_command(ctx: CommandContext):
    print(ctx.input)
    name = ctx.get_argument("name")
    return f"Hello, {name}!"


simple_builder.register(dispatcher)
print(dispatcher.execute("echo Mooling", {}))
