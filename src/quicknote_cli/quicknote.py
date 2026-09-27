from datetime import date, datetime
import argparse
import json
import sys
import os

DATA_DIR = os.path.expanduser("~/.local/share/quicknote")
DATA_FILE = os.path.join(DATA_DIR, "todos.json")
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
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(todos, f, indent=2)

def find_todo(todos, name):
    for todo in todos:
        if todo["name"].lower() == name.lower():
            return todo
        
    return None

def parse_date(date_str):

    if not date_str:
       return None

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strftime(date_str, fmt).date()
        except ValueError:
            continue

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

def cmd_priority(args):
    todos = load_todos()

    todo = find_todo(todos, args.name)

    if not todo:
        print(f'No todo named "{args.name}" found.')
        return

    current = todo.get("priority", 0)
    todo["priority"] = current + args.value if args.direction == "increase" else current - args.value
    save_todos(todos)

    print(f'Updated priority of "{args.name}": {current} -> {todo["priority"]}')

def cmd_edit(args):
    todos = load_todos()

    todo = find_todo(todos, args.name)

    if not todo:
        print(f'No todo named "{args.name}" found.')
        return

    field = args.field.lower()
    if field not in VALID_EDIT_FIELDS:
        print(f'Cannot edit field "{args.field}". Valid fiels: {",".join(VALID_EDIT_FIELDS)}')
        return

    if field == "priority":
        try:
            todo["priority"] = int(args.new_value)

        except ValueError:
            print("Priority must be an integer.")
            return
    else:
        todo[field] = args.new_value

    save_todos(todos)
    print(f'Updated "{args.name}": {field} -> {args.new_value}')

def cmd_important(args):
    todos = load_todos()
    if not todos:
        print("No todos yet. Create one with: todo.py create <name>")
        return
 
    if args.date:
        dated = [(t, parse_date(t.get("date", ""))) for t in todos]
        dated = [(t, d) for t, d in dated if d is not None]
        if not dated:
            print("No todos have a valid date (expected format: YYYY-MM-DD).")
            return
        today = date.today()
        nearest_gap = min(abs((d - today).days) for _, d in dated)
        nearest = [t for t, d in dated if abs((d - today).days) == nearest_gap]
        print(f"Nearest-date todo(s) (today is {today.isoformat()}):")
        for t in nearest:
            print(f'  {t["name"]}  date={t["date"]}  priority={t.get("priority", 0)}')
    else:
        max_priority = max(t.get("priority", 0) for t in todos)
        top = [t for t in todos if t.get("priority", 0) == max_priority]
        print(f"Highest-priority todo(s) (priority={max_priority}):")
        for t in top:
            print(f'  {t["name"]}  date={t.get("date") or "-"}  priority={t.get("priority", 0)}')

# --------------------------------------------------------------------------
# Parser setup
# --------------------------------------------------------------------------

def build_parser():
    parser = HelpOnErrorParser(
        prog="quicknote.py",
        description="A simple JSON-backed command-line todo list manager.",
        epilog=(
            "examples:\n"
            "   quicknote.py create \"get dinner\" 2026-10-01 3\n"
            "   quicknote.py list\n"
            "   quicknote.py delete \"get dinner\"\n"
            "   quicknote.py edit \"get dinner\" date 2026-10-05\n"
            "   quicknote.py priority \"get dinner\" increase 2\n"
            "   quicknote.py important\n"
            "   quicknote.py important --date\n\n"
            "data is stored in todos.json next to this script."
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

    p_priority = subparsers.add_parser(
        "priority", help="priority <name> <increase/decrease> <vaule>",
        description="Change a todo's priority. All arguments are required."
    )

    p_priority.add_argument("name", help="name of the todo")
    p_priority.add_argument("direction", choices=["increase", "decrease"], help="increase or decrease")
    p_priority.add_argument("value", type=int, help="interger amount to change the priority by")
    p_priority.set_defaults(func=cmd_priority)

    p_edit = subparsers.add_parser(
        "edit", help="edit <name> <field> <new_value>",
        description="Edit a todo's name, date and priority"
    )

    p_edit.add_argument("name", help="name of the todo to edit")
    p_edit.add_argument("field", help="Fields to edit: name, date, priority")
    p_edit.add_argument("new_value", help="new value for the field")
    p_edit.set_defaults(func=cmd_edit)

    p_important = subparsers.add_parser(
        "important", help="important [-d/--date] - show highest priority, or nearest date todo(s)",
        description=(
            "Show the highest-priority todo(s). With -d/--date, show the "
            "todo(s) whose date is nearest to today instead."
        ),
    )
    
    p_important.add_argument(
        "-d", "--date", action="store_true",
        help="show the nearest-date todo(s) instead of the highest-priority one(s)",
    )
    p_important.set_defaults(func=cmd_important)

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