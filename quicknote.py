import argparse
import sys

file = []

# --------------------------------------------------------------------------
# Storage helpers
# --------------------------------------------------------------------------

def load_todos():
    return file

def save_todos(todos):
    file.append(todos)


# --------------------------------------------------------------------------
# this printes full help (not just a usage line) on any error,
# example: when a required argument is missing.
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
    print(f'Created "{todo["name"]}" (date={todo["date"] or "-"}), (priority={todo["priority"]})')

# --------------------------------------------------------------------------
# Parser setup
# --------------------------------------------------------------------------

def build_praser():
    parser = HelpOnErrorParser(
        prog="quicknote.py",
        description="A simple JSON-backed command-line todo list manager.",
        epilog=(
            "Examples:\n"
            "   todo.py create \"get diner\" 2026-10-01 3\n"
        ),

        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command", metavar="{}",
        parser_class=HelpOnErrorParser
    )

    p_create = subparsers.add_parser(
        "create", help="create <name> [date] [priority]",
        description="Create a new todo. name is required date and priority are optional."
    )

    return parser

# --------------------------------------------------------------------------
# Main Function
# --------------------------------------------------------------------------
def main():
    parser = build_praser()
    args = parser.parse_args()

    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(0)

    args.func(args)

if __name__ == "__main__":
    main()