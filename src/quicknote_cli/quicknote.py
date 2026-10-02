from datetime import date, datetime
import argparse
import json
import os
import sys


def get_data_dir():
    """Return the platform-specific directory used to store QuickNote data."""
    if sys.platform.startswith("win"):
        # Windows: %LOCALAPPDATA%\QuickNote
        local_app_data = os.environ.get("LOCALAPPDATA")

        if local_app_data:
            return os.path.join(local_app_data, "QuickNote")

        # Fallback if LOCALAPPDATA is unavailable.
        return os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Local",
            "QuickNote",
        )

    if sys.platform == "darwin":
        # macOS: ~/Library/Application Support/QuickNote
        return os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            "QuickNote",
        )

    # Linux and other Unix-like systems:
    # ~/.local/share/quicknote
    data_home = os.environ.get("XDG_DATA_HOME")

    if data_home:
        return os.path.join(data_home, "quicknote")

    return os.path.join(
        os.path.expanduser("~"),
        ".local",
        "share",
        "quicknote",
    )


DATA_DIR = get_data_dir()
DATA_FILE = os.path.join(DATA_DIR, "todos.json")
VALID_EDIT_FIELDS = ("name", "date", "priority")


# --------------------------------------------------------------------------
# Storage helpers
# --------------------------------------------------------------------------

def load_todos():
    """Load todos from the local JSON file."""
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            todos = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(todos, list):
        return []

    # Backwards compatibility:
    # old todos do not have a "completed" field.
    valid_todos = []

    for todo in todos:
        if not isinstance(todo, dict):
            continue

        todo.setdefault("name", "")
        todo.setdefault("date", "")
        todo.setdefault("priority", 0)
        todo.setdefault("completed", False)

        valid_todos.append(todo)

    return valid_todos


def save_todos(todos):
    """Save todos to the local JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(todos, file, indent=2)


def find_todo(todos, name):
    """Find a todo by name, ignoring capitalization."""
    for todo in todos:
        if todo.get("name", "").lower() == name.lower():
            return todo

    return None


# --------------------------------------------------------------------------
# Date helpers
# --------------------------------------------------------------------------

def parse_date(date_str):
    """
    Parse a supported date string.

    Supported formats:
    - YYYY-MM-DD
    - YYYY/MM/DD
    - MM/DD/YYYY
    - DD-MM-YYYY

    Returns a datetime.date or None if invalid.
    """
    if not date_str:
        return None

    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d-%m-%Y",
    ):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def validate_date(date_str):
    """Return True if the date is empty or valid."""
    return not date_str or parse_date(date_str) is not None


# --------------------------------------------------------------------------
# Display helpers
# --------------------------------------------------------------------------

def display_status(todo):
    """Return a readable status for a todo."""
    return "Done" if todo.get("completed", False) else "Pending"


# --------------------------------------------------------------------------
# Parser that prints full help on errors
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
        print(f'A todo named "{args.name}" already exists.')
        return

    if not validate_date(args.date):
        print(
            "Invalid date. Use YYYY-MM-DD, YYYY/MM/DD, "
            "MM/DD/YYYY, or DD-MM-YYYY."
        )
        return

    todo = {
        "name": args.name,
        "date": args.date or "",
        "priority": args.priority if args.priority is not None else 0,
        "completed": False,
    }

    todos.append(todo)
    save_todos(todos)

    print(
        f'Created "{todo["name"]}" '
        f'(date={todo["date"] or "-"}, '
        f'priority={todo["priority"]}, '
        f'status=Pending)'
    )


def cmd_list(args):
    todos = load_todos()

    if not todos:
        print(
            "No todos yet. "
            "Create one with: quicknote create <name>"
        )
        return

    todos_sorted = sorted(
        todos,
        key=lambda todo: todo.get("priority", 0),
        reverse=True,
    )

    name_width = max(
        len(todo.get("name", ""))
        for todo in todos_sorted
    ) + 2

    date_width = 14
    priority_width = 10
    status_width = 10

    print(
        f'{"NAME":<{name_width}}'
        f'{"DATE":<{date_width}}'
        f'{"PRIORITY":<{priority_width}}'
        f'{"STATUS":<{status_width}}'
    )

    print(
        "-"
        * (
            name_width
            + date_width
            + priority_width
            + status_width
        )
    )

    for todo in todos_sorted:
        print(
            f'{todo.get("name", ""):<{name_width}}'
            f'{(todo.get("date") or "-"):<{date_width}}'
            f'{todo.get("priority", 0):<{priority_width}}'
            f'{display_status(todo):<{status_width}}'
        )


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

    if args.value < 0:
        print(
            "Priority change amount must be "
            "a non-negative integer."
        )
        return

    current = todo.get("priority", 0)

    if args.direction == "increase":
        todo["priority"] = current + args.value
    else:
        todo["priority"] = current - args.value

    save_todos(todos)

    print(
        f'Updated priority of "{args.name}": '
        f'{current} -> {todo["priority"]}'
    )


def cmd_edit(args):
    todos = load_todos()

    todo = find_todo(todos, args.name)

    if not todo:
        print(f'No todo named "{args.name}" found.')
        return

    field = args.field.lower()

    if field not in VALID_EDIT_FIELDS:
        print(
            f'Cannot edit field "{args.field}". '
            f"Valid fields: {', '.join(VALID_EDIT_FIELDS)}"
        )
        return

    if field == "priority":
        try:
            todo["priority"] = int(args.new_value)
        except ValueError:
            print("Priority must be an integer.")
            return

    elif field == "date":
        if not validate_date(args.new_value):
            print(
                "Invalid date. Use YYYY-MM-DD, YYYY/MM/DD, "
                "MM/DD/YYYY, or DD-MM-YYYY."
            )
            return

        todo["date"] = args.new_value

    else:
        new_name = args.new_value.strip()

        if not new_name:
            print("Todo name cannot be empty.")
            return

        existing_todo = find_todo(todos, new_name)

        if existing_todo is not None and existing_todo is not todo:
            print(f'A todo named "{new_name}" already exists.')
            return

        todo[field] = new_name

    save_todos(todos)

    print(
        f'Updated "{args.name}": '
        f'{field} -> {args.new_value}'
    )


def cmd_complete(args):
    todos = load_todos()

    todo = find_todo(todos, args.name)

    if not todo:
        print(f'No todo named "{args.name}" found.')
        return

    todo["completed"] = not args.pending

    save_todos(todos)

    print(
        f'Updated "{args.name}": '
        f'status -> {display_status(todo)}'
    )


def cmd_important(args):
    todos = load_todos()

    if not todos:
        print(
            "No todos yet. "
            "Create one with: quicknote create <name>"
        )
        return

    if args.date:
        dated = [
            (todo, parse_date(todo.get("date", "")))
            for todo in todos
        ]

        dated = [
            (todo, parsed_date)
            for todo, parsed_date in dated
            if parsed_date is not None
        ]

        if not dated:
            print("No todos have a valid date.")
            return

        today = date.today()

        nearest_gap = min(
            abs((parsed_date - today).days)
            for _, parsed_date in dated
        )

        nearest = [
            todo
            for todo, parsed_date in dated
            if abs((parsed_date - today).days) == nearest_gap
        ]

        print(
            f"Nearest-date todo(s) "
            f"(today is {today.isoformat()}):"
        )

        for todo in nearest:
            print(
                f'  {todo.get("name", "")}  '
                f'date={todo.get("date") or "-"}  '
                f'priority={todo.get("priority", 0)}  '
                f'status={display_status(todo)}'
            )

    else:
        max_priority = max(
            todo.get("priority", 0)
            for todo in todos
        )

        top = [
            todo
            for todo in todos
            if todo.get("priority", 0) == max_priority
        ]

        print(
            f"Highest-priority todo(s) "
            f"(priority={max_priority}):"
        )

        for todo in top:
            print(
                f'  {todo.get("name", "")}  '
                f'date={todo.get("date") or "-"}  '
                f'priority={todo.get("priority", 0)}  '
                f'status={display_status(todo)}'
            )


# --------------------------------------------------------------------------
# Parser setup
# --------------------------------------------------------------------------

def build_parser():
    parser = HelpOnErrorParser(
        prog="quicknote",
        description=(
            "A simple JSON-backed command-line "
            "todo list manager."
        ),
        epilog=(
            "examples:\n"
            '  quicknote create "Get dinner" 2026-10-01 3\n'
            "  quicknote list\n"
            '  quicknote delete "Get dinner"\n'
            '  quicknote edit "Get dinner" date 2026-10-05\n'
            '  quicknote priority "Get dinner" increase 2\n'
            '  quicknote complete "Get dinner"\n'
            '  quicknote complete "Get dinner" --pending\n'
            "  quicknote important\n"
            "  quicknote important --date\n\n"
            f"data is stored locally at {DATA_FILE}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar=(
            "{create,list,delete,edit,"
            "priority,complete,important}"
        ),
        parser_class=HelpOnErrorParser,
    )

    # ----------------------------------------------------------------------
    # create
    # ----------------------------------------------------------------------

    p_create = subparsers.add_parser(
        "create",
        help="create <name> [date] [priority]",
        description=(
            "Create a new todo. "
            "Name is required; date and priority are optional."
        ),
    )

    p_create.add_argument(
        "name",
        help="name of the todo",
    )

    p_create.add_argument(
            "priority",
            nargs="?",
            type=int,
            default=None,
            help="priority as an integer",
        )

    p_create.add_argument(
        "date",
        nargs="?",
        default=None,
        help="due date, e.g. 2026-10-01",
    )

    p_create.set_defaults(func=cmd_create)

    # ----------------------------------------------------------------------
    # list
    # ----------------------------------------------------------------------

    p_list = subparsers.add_parser(
        "list",
        help="list all todos",
        description="List all todos, sorted by priority.",
    )

    p_list.set_defaults(func=cmd_list)

    # ----------------------------------------------------------------------
    # delete
    # ----------------------------------------------------------------------

    p_delete = subparsers.add_parser(
        "delete",
        help="delete <name>",
        description="Delete a todo by name.",
    )

    p_delete.add_argument(
        "name",
        help="name of the todo to delete",
    )

    p_delete.set_defaults(func=cmd_delete)

    # ----------------------------------------------------------------------
    # priority
    # ----------------------------------------------------------------------

    p_priority = subparsers.add_parser(
        "priority",
        help="priority <name> <increase/decrease> <value>",
        description="Change a todo's priority.",
    )

    p_priority.add_argument(
        "name",
        help="name of the todo",
    )

    p_priority.add_argument(
        "direction",
        choices=["increase", "decrease"],
        help="increase or decrease",
    )

    p_priority.add_argument(
        "value",
        type=int,
        help="integer amount to change the priority by",
    )

    p_priority.set_defaults(func=cmd_priority)

    # ----------------------------------------------------------------------
    # edit
    # ----------------------------------------------------------------------

    p_edit = subparsers.add_parser(
        "edit",
        help="edit <name> <field> <new_value>",
        description=(
            "Edit a todo's name, date, or priority."
        ),
    )

    p_edit.add_argument(
        "name",
        help="name of the todo to edit",
    )

    p_edit.add_argument(
        "field",
        help="field to edit: name, date, or priority",
    )

    p_edit.add_argument(
        "new_value",
        help="new value for the field",
    )

    p_edit.set_defaults(func=cmd_edit)

    # ----------------------------------------------------------------------
    # complete
    # ----------------------------------------------------------------------

    p_complete = subparsers.add_parser(
        "complete",
        help="complete <name> [--pending]",
        description=(
            "Mark a todo as completed, "
            "or return it to pending."
        ),
    )

    p_complete.add_argument(
        "name",
        help="name of the todo",
    )

    p_complete.add_argument(
        "--pending",
        action="store_true",
        help="mark the todo as pending",
    )

    p_complete.set_defaults(func=cmd_complete)

    # ----------------------------------------------------------------------
    # important
    # ----------------------------------------------------------------------

    p_important = subparsers.add_parser(
        "important",
        help="show highest-priority or nearest-date todos",
        description=(
            "Show the highest-priority todo(s). "
            "With -d/--date, show the todo(s) "
            "whose date is nearest to today instead."
        ),
    )

    p_important.add_argument(
        "-d",
        "--date",
        action="store_true",
        help=(
            "show the nearest-date todo(s) "
            "instead of highest-priority ones"
        ),
    )

    p_important.set_defaults(func=cmd_important)

    return parser


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    parser = build_parser()

    args = parser.parse_args()

    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()