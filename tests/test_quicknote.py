import json
import os
from datetime import date

import pytest

from quicknote_cli import quicknote


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """Give each test its own temporary QuickNote data file."""
    data_dir = tmp_path / "quicknote"
    data_file = data_dir / "todos.json"

    monkeypatch.setattr(
        quicknote,
        "DATA_DIR",
        str(data_dir),
    )

    monkeypatch.setattr(
        quicknote,
        "DATA_FILE",
        str(data_file),
    )

    return data_file


# --------------------------------------------------------------------------
# Storage tests
# --------------------------------------------------------------------------

def test_storage_persists(isolated_storage):
    todos = [
        {
            "name": "Persistent task",
            "date": "2026-10-05",
            "priority": 4,
            "completed": False,
        }
    ]

    quicknote.save_todos(todos)

    assert isolated_storage.exists()

    loaded = quicknote.load_todos()

    assert loaded == todos


def test_legacy_todo_gets_completion_field(isolated_storage):
    """Old todos without 'completed' should still load safely."""
    isolated_storage.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        isolated_storage,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            [
                {
                    "name": "Old todo",
                    "date": "",
                    "priority": 2,
                }
            ],
            file,
        )

    todos = quicknote.load_todos()

    assert todos[0]["completed"] is False


# --------------------------------------------------------------------------
# Create tests
# --------------------------------------------------------------------------

def test_create_todo(isolated_storage):
    args = type(
        "Args",
        (),
        {
            "name": "Homework",
            "date": "2026-10-05",
            "priority": 3,
        },
    )()

    quicknote.cmd_create(args)

    todos = quicknote.load_todos()

    assert len(todos) == 1
    assert todos[0]["name"] == "Homework"
    assert todos[0]["date"] == "2026-10-05"
    assert todos[0]["priority"] == 3
    assert todos[0]["completed"] is False


def test_create_todo_with_invalid_date(
    isolated_storage,
    capsys,
):
    args = type(
        "Args",
        (),
        {
            "name": "Bad date",
            "date": "2026-99-99",
            "priority": 1,
        },
    )()

    quicknote.cmd_create(args)

    output = capsys.readouterr().out

    assert "Invalid date" in output
    assert quicknote.load_todos() == []


# --------------------------------------------------------------------------
# List tests
# --------------------------------------------------------------------------

def test_list_empty(isolated_storage, capsys):
    args = type("Args", (), {})()

    quicknote.cmd_list(args)

    output = capsys.readouterr().out

    assert "No todos yet" in output


def test_list_sorts_by_priority(isolated_storage, capsys):
    todos = [
        {
            "name": "Low",
            "date": "",
            "priority": 1,
            "completed": False,
        },
        {
            "name": "High",
            "date": "",
            "priority": 10,
            "completed": False,
        },
    ]

    quicknote.save_todos(todos)

    args = type("Args", (), {})()

    quicknote.cmd_list(args)

    output = capsys.readouterr().out

    high_position = output.index("High")
    low_position = output.index("Low")

    assert high_position < low_position


def test_list_shows_completion_status(
    isolated_storage,
    capsys,
):
    todos = [
        {
            "name": "Finished task",
            "date": "",
            "priority": 1,
            "completed": True,
        },
        {
            "name": "Pending task",
            "date": "",
            "priority": 2,
            "completed": False,
        },
    ]

    quicknote.save_todos(todos)

    args = type("Args", (), {})()

    quicknote.cmd_list(args)

    output = capsys.readouterr().out

    assert "Finished task" in output
    assert "Done" in output
    assert "Pending" in output


# --------------------------------------------------------------------------
# Delete tests
# --------------------------------------------------------------------------

def test_delete_todo(isolated_storage):
    todos = [
        {
            "name": "Delete me",
            "date": "",
            "priority": 1,
            "completed": False,
        }
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "name": "Delete me",
        },
    )()

    quicknote.cmd_delete(args)

    assert quicknote.load_todos() == []


# --------------------------------------------------------------------------
# Edit tests
# --------------------------------------------------------------------------

def test_edit_todo(isolated_storage):
    todos = [
        {
            "name": "Homework",
            "date": "2026-10-05",
            "priority": 1,
            "completed": False,
        }
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "name": "Homework",
            "field": "priority",
            "new_value": "5",
        },
    )()

    quicknote.cmd_edit(args)

    updated = quicknote.load_todos()

    assert updated[0]["priority"] == 5


def test_edit_date(isolated_storage):
    todos = [
        {
            "name": "Homework",
            "date": "2026-10-05",
            "priority": 1,
            "completed": False,
        }
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "name": "Homework",
            "field": "date",
            "new_value": "2026-11-01",
        },
    )()

    quicknote.cmd_edit(args)

    assert quicknote.load_todos()[0]["date"] == "2026-11-01"


def test_edit_invalid_priority(
    isolated_storage,
    capsys,
):
    todos = [
        {
            "name": "Homework",
            "date": "",
            "priority": 3,
            "completed": False,
        }
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "name": "Homework",
            "field": "priority",
            "new_value": "not-a-number",
        },
    )()

    quicknote.cmd_edit(args)

    output = capsys.readouterr().out

    assert "Priority must be an integer" in output
    assert quicknote.load_todos()[0]["priority"] == 3


# --------------------------------------------------------------------------
# Priority tests
# --------------------------------------------------------------------------

def test_increase_priority(isolated_storage):
    todos = [
        {
            "name": "Task",
            "date": "",
            "priority": 2,
            "completed": False,
        }
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "name": "Task",
            "direction": "increase",
            "value": 3,
        },
    )()

    quicknote.cmd_priority(args)

    assert quicknote.load_todos()[0]["priority"] == 5


def test_decrease_priority(isolated_storage):
    todos = [
        {
            "name": "Task",
            "date": "",
            "priority": 5,
            "completed": False,
        }
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "name": "Task",
            "direction": "decrease",
            "value": 2,
        },
    )()

    quicknote.cmd_priority(args)

    assert quicknote.load_todos()[0]["priority"] == 3


def test_invalid_priority_value(
    isolated_storage,
    capsys,
):
    todos = [
        {
            "name": "Task",
            "date": "",
            "priority": 5,
            "completed": False,
        }
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "name": "Task",
            "direction": "increase",
            "value": -1,
        },
    )()

    quicknote.cmd_priority(args)

    output = capsys.readouterr().out

    assert "non-negative" in output
    assert quicknote.load_todos()[0]["priority"] == 5


def test_priority_parser_rejects_non_integer():
    parser = quicknote.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "priority",
                "Task",
                "increase",
                "abc",
            ]
        )


# --------------------------------------------------------------------------
# Date tests
# --------------------------------------------------------------------------

def test_parse_valid_dates():
    assert quicknote.parse_date("2026-10-05") == date(
        2026,
        10,
        5,
    )

    assert quicknote.parse_date("2026/10/05") == date(
        2026,
        10,
        5,
    )

    assert quicknote.parse_date("10/05/2026") == date(
        2026,
        10,
        5,
    )

    assert quicknote.parse_date("05-10-2026") == date(
        2026,
        10,
        5,
    )


def test_parse_invalid_dates():
    assert quicknote.parse_date("not-a-date") is None
    assert quicknote.parse_date("2026-99-99") is None
    assert quicknote.parse_date("2026-02-30") is None
    assert quicknote.parse_date("") is None


# --------------------------------------------------------------------------
# Important/date selection tests
# --------------------------------------------------------------------------

def test_important_uses_highest_priority(
    isolated_storage,
    capsys,
):
    todos = [
        {
            "name": "Low",
            "date": "",
            "priority": 1,
            "completed": False,
        },
        {
            "name": "High",
            "date": "",
            "priority": 10,
            "completed": False,
        },
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "date": False,
        },
    )()

    quicknote.cmd_important(args)

    output = capsys.readouterr().out

    assert "High" in output
    assert "Low" not in output


def test_date_based_selection(
    isolated_storage,
    monkeypatch,
    capsys,
):
    todos = [
        {
            "name": "Soon",
            "date": "2026-10-02",
            "priority": 1,
            "completed": False,
        },
        {
            "name": "Later",
            "date": "2026-12-25",
            "priority": 10,
            "completed": False,
        },
    ]

    quicknote.save_todos(todos)

    class FakeDate:
        @classmethod
        def today(cls):
            return date(2026, 10, 1)

    monkeypatch.setattr(
        quicknote,
        "date",
        FakeDate,
    )

    args = type(
        "Args",
        (),
        {
            "date": True,
        },
    )()

    quicknote.cmd_important(args)

    output = capsys.readouterr().out

    assert "Soon" in output
    assert "Later" not in output


# --------------------------------------------------------------------------
# Completion tests
# --------------------------------------------------------------------------

def test_complete_todo(isolated_storage):
    todos = [
        {
            "name": "Finish project",
            "date": "",
            "priority": 3,
            "completed": False,
        }
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "name": "Finish project",
            "pending": False,
        },
    )()

    quicknote.cmd_complete(args)

    assert quicknote.load_todos()[0]["completed"] is True


def test_mark_todo_pending(isolated_storage):
    todos = [
        {
            "name": "Finish project",
            "date": "",
            "priority": 3,
            "completed": True,
        }
    ]

    quicknote.save_todos(todos)

    args = type(
        "Args",
        (),
        {
            "name": "Finish project",
            "pending": True,
        },
    )()

    quicknote.cmd_complete(args)

    assert quicknote.load_todos()[0]["completed"] is False


# --------------------------------------------------------------------------
# Cross-platform storage path tests
# --------------------------------------------------------------------------

def test_windows_data_dir(monkeypatch):
    monkeypatch.setattr(
        quicknote.sys,
        "platform",
        "win32",
    )

    monkeypatch.setenv(
        "LOCALAPPDATA",
        r"C:\Users\Test\AppData\Local",
    )

    result = quicknote.get_data_dir()

    assert result.replace("\\", "/") == (
        "C:/Users/Test/AppData/Local/QuickNote"
    )


def test_windows_data_dir_fallback(monkeypatch):
    monkeypatch.setattr(
        quicknote.sys,
        "platform",
        "win32",
    )

    monkeypatch.delenv(
        "LOCALAPPDATA",
        raising=False,
    )

    expected = os.path.join(
        os.path.expanduser("~"),
        "AppData",
        "Local",
        "QuickNote",
    )

    assert quicknote.get_data_dir() == expected


def test_macos_data_dir(monkeypatch):
    monkeypatch.setattr(
        quicknote.sys,
        "platform",
        "darwin",
    )

    monkeypatch.delenv(
        "XDG_DATA_HOME",
        raising=False,
    )

    expected = os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Application Support",
        "QuickNote",
    )

    assert quicknote.get_data_dir() == expected


def test_linux_data_dir(monkeypatch):
    monkeypatch.setattr(
        quicknote.sys,
        "platform",
        "linux",
    )

    monkeypatch.delenv(
        "XDG_DATA_HOME",
        raising=False,
    )

    expected = os.path.join(
        os.path.expanduser("~"),
        ".local",
        "share",
        "quicknote",
    )

    assert quicknote.get_data_dir() == expected


def test_linux_xdg_data_dir(monkeypatch):
    monkeypatch.setattr(
        quicknote.sys,
        "platform",
        "linux",
    )

    monkeypatch.setenv(
        "XDG_DATA_HOME",
        "/tmp/test-data",
    )

    expected = os.path.join(
        "/tmp/test-data",
        "quicknote",
    )

    assert quicknote.get_data_dir() == expected