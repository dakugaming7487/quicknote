# QuickNote

A lightweight command-line Todo manager written in Python.

QuickNote stores Todos as JSON and provides commands for creating, viewing, editing, deleting, and prioritizing tasks directly from the terminal.

## Features

- Create Todo with an optional date and priority
- List Todos sorted by priority
- Delete Todos by name
- Edit a Todo's name, date, or priority
- Increase or decrease a Todo's priority
- Find the highest-priority Todo 
- Find the Todo with the nearest date to today
- JSON-based local storage
- Helpful command-line error messages and help output
- No external runtime dependencies

## Requirements

- Python 3.9 or newer

## Installation

Clone the repository:

```bash
git clone https://github.com/dakugaming7487/quicknote
cd <repo-directory>
```

Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

Install QuickNote:

```bash
pip install .
```

for development, Install it in editable mode:
```bash
pip install -e .
```

### Usage

After installation, run
```bash
quicknote
```

You can view available commands with:
```bash
quicknote --help
```

### Create a Todo 
Create a Todo with only name:
```bash
quicknote create "Get dinner"
```
you can optionally provide a date and priority:
```bash
quicknote create "Get dinner" 2026-20-1 3
```

### List Todos
```bash
quicknote list
```

Todos are displayed sorted by priority

### Delete a Todo
```bash
quicknote delete "Get dinner"
```

### Edit a Todo
You can edit the name, date, or priority of an existing todo.

for example:
```bash
quicknote edit "Get dinner" date 2026-10-5
```

Or:
```bash
quicknote edit "Get dinner" priority 5
```

### Change Priority
Increase a todo's priority:
```bash
quicknote priority "Get dinner" increase 2
```

Decrease a todo's Priority:
```bash
quicknote priority "Get dinner" decrease 1
```

### Find Important Todos
Decrease a todo's priority:

    quicknote priority "Get dinner" decrease 1

### Find Important Todos

Show the highest-priority todo:

    quicknote important

Show the todo or todos whose date is nearest to today:

    quicknote important --date

## Data Storage

QuickNote uses JSON for local todo storage.

Each todo contains:

- `name` - the name of the task
- `date` - the optional due date
- `priority` - an integer representing its priority

Example:

    [
      {
        "name": "Get dinner",
        "date": "2026-10-01",
        "priority": 3
      }
    ]

## Project Structure

    .
    ├── LICENSE
    ├── README.md
    ├── pyproject.toml
    ├── src/
    │   └── quicknote_cli/
    │       ├── __init__.py
    │       └── quicknote.py
    └── tests/
## Development

Install the project in editable mode:

    pip install -e .

Build the package:

    python -m build

The build system creates distribution files inside the `dist/` directory.

Run tests with:

    pytest

## License

See the `LICENSE` file for the license used by this project.

