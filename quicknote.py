import argparse
import sys

DATA_FILE = []
VALID_EDIT_FIELDS = ("name", "date", "priority")


# --------------------------------------------------------------------------
# Storage helpers
# --------------------------------------------------------------------------

def load_todos():
    return DATA_FILE

def save_todos(todos):
    DATA_FILE.append(todos)


# --------------------------------------------------------------------------
# Parser that prints full help (not just a usage line) on any error,
# e.g. when a required argument is missing.
# --------------------------------------------------------------------------
class HelpOnErrorParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"error: {message}\n\n")
        self.print_help()
        sys.exit(2)


# --------------------------------------------------------------------------
# Command handlers
# --------------------------------------------------------------------------

def cmd_create(args):
    todos = load_todos()
    todo = {
        "name": args.name,
        "date": args.date or "",
        "priority": args.priority if args.priority is not None else 0,
    }
    todos.append(todo)
    save_todos(todos)
    print(f'Created "{todo["name"]}" (date={todo["date"] or "-"}, priority={todo["priority"]})')

# --------------------------------------------------------------------------
# Parser setup
# --------------------------------------------------------------------------

def build_parser():
    parser = HelpOnErrorParser(
        prog="todo.py",
        description="A simple JSON-backed command-line todo list manager.",
        epilog=(
            "examples:\n"
            "  todo.py create \"get dinner\" 2026-10-01 3\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command", metavar="{create,list,delete,priority,edit,important}",
        parser_class=HelpOnErrorParser,
    )

    p_create = subparsers.add_parser(
        "create", help="create <name> [date] [priority]",
        description="Create a new todo. name is required; date and priority are optional.",
    )
    p_create.add_argument("name", help="name of the todo")
    p_create.add_argument("date", nargs="?", default=None, help="due date (optional), e.g. 2026-10-01")
    p_create.add_argument("priority", nargs="?", type=int, default=None, help="priority as an integer (optional)")
    p_create.set_defaults(func=cmd_create)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()