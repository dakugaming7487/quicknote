import argparse
import json
import sys
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")
VALID_EDIT_FIELDS = ("name", "date", "priority")


# --------------------------------------------------------------------------
# Storage helpers
# --------------------------------------------------------------------------

def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []

def save_todos(todos):
    with open(DATA_FILE, "w") as f:
        json.dump(todos, f, indent=2)

def find_todo(todos, name):
    for todo in todos:
        if todo["name"].lower() == name.lower():
            return todo
        
    return None


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

    if find_todo(todos, args.name):
        print(f'A todo has the same name as the newly entered one')
        return

    todo = {
        "name": args.name,
        "date": args.date or "",
        "priority": args.priority if args.priority is not None else 0,
    }
    todos.append(todo)
    save_todos(todos)
    print(f'Created "{todo["name"]}" (date={todo["date"] or "-"}, priority={todo["priority"]})')

def cmd_list(args):
    todos = load_todos()

    if not todos:
        print("No todo yet. Create one right now with: quicknote.py create <name>")
        return

    todos_sorted = sorted(todos, key=lambda t: t.get("priority", 0), reverse=True)

    name_w = max(len(t["name"]) for t in todos_sorted) + 2

    print(f'{"NAME":<{name_w}}{"date":<14}{"PRIORITY":<10}')

    print("-" * (name_w + 24))

    for t in todos_sorted:
        print(f'{t["name"]:<{name_w}}{(t.get("date") or "-"):<14}{t.get("priority", 0):<10}')

def cmd_delete(args):

    todos = load_todos()

    todo = find_todo(todos, args.name)

    if not todo:
        print(f'Todo named "{args.name}" not found.')
        return

    todos.remove(todo)
    save_todos(todos)
    print(f'Deleted "{args.name}"')

# --------------------------------------------------------------------------
# Parser setup
# --------------------------------------------------------------------------

def build_parser():
    parser = HelpOnErrorParser(
        prog="quicknote.py",
        description="A simple JSON-backed command-line todo list manager.",
        epilog=(
            "examples:\n"
            "  quicknote.py create \"get dinner\" 2026-10-01 3\n"
            "  quicknote.py list\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command", metavar="{create,list,delete,edit}",
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

    p_list = subparsers.add_parser(
        "list", help="list all todos",
        description="List all todos, sorted by priority.",
    )

    p_list.set_defaults(func=cmd_list)

    p_delete = subparsers.add_parser(
        "delete", help="delete <name>",
        description="Delete a todo by name. name is required"
    )

    p_delete.add_argument("name", help="name of the todo to be removed")
    p_delete.set_defaults(func=cmd_delete)

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