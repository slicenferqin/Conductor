"""Tests for task queue."""

import pytest
from conductor.core.task_queue import Task, TaskQueue, TaskStatus


def test_task_creation():
    """Test task creation."""
    task = Task(requirement="Build a todo app")
    assert task.requirement == "Build a todo app"
    assert task.status == TaskStatus.PENDING
    assert task.progress == 0


def test_task_queue_add_and_get():
    """Test adding and getting tasks."""
    queue = TaskQueue()
    task = Task(requirement="Build a todo app")

    task_id = queue.add(task)
    retrieved = queue.get(task_id)

    assert retrieved is not None
    assert retrieved.requirement == "Build a todo app"


def test_task_queue_list_all():
    """Test listing all tasks."""
    queue = TaskQueue()
    queue.add(Task(requirement="Task 1"))
    queue.add(Task(requirement="Task 2"))

    tasks = queue.list_all()
    assert len(tasks) == 2


def test_task_queue_get_pending():
    """Test getting pending tasks."""
    queue = TaskQueue()

    task1 = Task(requirement="Pending task")
    task2 = Task(requirement="Running task", status=TaskStatus.RUNNING)

    queue.add(task1)
    queue.add(task2)

    pending = queue.get_pending()
    assert len(pending) == 1
    assert pending[0].requirement == "Pending task"