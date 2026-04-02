"""Tests for the task executor and classifier."""

from prollama.executor.task_executor import TaskExecutor, classify_complexity, classify_type
from prollama.models import Task, TaskComplexity, TaskStatus, TaskType


class TestComplexityClassifier:
    """Test the heuristic complexity classifier."""

    def test_simple_tasks(self):
        simple_descriptions = [
            "Fix typo in README",
            "Add missing type hints to utils",
            "Fix formatting in config.py",
            "Add docstring to main function",
            "Fix indent in test file",
            "Fix spelling in comments",
            "Update changelog entry",
        ]
        for desc in simple_descriptions:
            task = Task(description=desc)
            assert classify_complexity(task) == TaskComplexity.SIMPLE, (
                f"Expected SIMPLE for: {desc}"
            )

    def test_medium_tasks(self):
        medium_descriptions = [
            "Fix the TypeError bug in auth module",
            "Handle connection timeout exception",
            "Fix null pointer error in parser",
            "Add error handling for API failures",
            "Write tests for payment module",
        ]
        for desc in medium_descriptions:
            task = Task(description=desc)
            assert classify_complexity(task) == TaskComplexity.MEDIUM, (
                f"Expected MEDIUM for: {desc}"
            )

    def test_hard_tasks(self):
        hard_descriptions = [
            "Refactor PaymentService to use strategy pattern",
            "Extract authentication into separate module",
            "Add new REST endpoint for user profiles",
            "Implement feature flag system",
            "Fix security vulnerability in session handling",
        ]
        for desc in hard_descriptions:
            task = Task(description=desc)
            assert classify_complexity(task) == TaskComplexity.HARD, (
                f"Expected HARD for: {desc}"
            )

    def test_very_hard_tasks(self):
        very_hard_descriptions = [
            "Architect multi-file migration for new schema",
            "Redesign the entire caching layer",
            "Multi-file architecture overhaul",
            "Database migration to new schema",
        ]
        for desc in very_hard_descriptions:
            task = Task(description=desc)
            assert classify_complexity(task) == TaskComplexity.VERY_HARD, (
                f"Expected VERY_HARD for: {desc}"
            )


class TestTypeClassifier:
    """Test the task type classifier."""

    def test_fix_type(self):
        for desc in ["Fix crash on login", "Fix the production bug", "Patch the error"]:
            task = Task(description=desc)
            assert classify_type(task) == TaskType.FIX

    def test_refactor_type(self):
        for desc in ["Refactor auth module", "Extract common utils", "Rename variables"]:
            task = Task(description=desc)
            assert classify_type(task) == TaskType.REFACTOR

    def test_feature_type(self):
        for desc in ["Add user registration", "Implement search API", "Create admin dashboard"]:
            task = Task(description=desc)
            assert classify_type(task) == TaskType.FEATURE

    def test_security_type(self):
        for desc in ["Fix SQL injection vulnerability", "Patch CVE-2025-1234", "Fix XSS in forms"]:
            task = Task(description=desc)
            assert classify_type(task) == TaskType.SECURITY

    def test_test_type(self):
        for desc in ["Add test coverage for auth", "Write unit tests", "Improve test spec"]:
            task = Task(description=desc)
            assert classify_type(task) == TaskType.TEST


class TestTaskExecutorInit:
    """Test executor initialization (without actual LLM calls)."""

    def test_executor_creates_with_config(self, config_ollama):
        executor = TaskExecutor(config_ollama)
        assert executor.config == config_ollama
        assert executor.router is not None
        assert executor.pipeline is not None

    def test_solve_fails_with_no_providers(self, config_empty):
        executor = TaskExecutor(config_empty)
        task = Task(description="Fix something")
        result = executor.solve(task)
        assert result.status == TaskStatus.FAILED
        assert "No available models" in result.error_message

    def test_task_classification_applied(self, config_ollama):
        executor = TaskExecutor(config_ollama)
        task = Task(description="Refactor the auth module")
        # The solve will fail (no actual LLM) but classification should run
        executor.solve(task)
        assert task.complexity == TaskComplexity.HARD
        assert task.task_type == TaskType.REFACTOR
