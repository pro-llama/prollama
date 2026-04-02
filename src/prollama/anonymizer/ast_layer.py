"""Layer 3: AST-based identifier anonymization via tree-sitter.

Parses source code into an AST, identifies class names, function names,
variable names, and other identifiers that reveal business logic, then
replaces them with generic placeholders while preserving code structure.

Requires: pip install prollama[ast]
"""

from __future__ import annotations

from dataclasses import dataclass, field

from prollama.models import AnonymizationMapping

# ---------------------------------------------------------------------------
# Language-specific node types to anonymize
# ---------------------------------------------------------------------------

# Node types whose text content should be anonymized
PYTHON_TARGETS = {
    # Definitions
    "identifier",  # catches function names, variable names, parameters
}

JAVASCRIPT_TARGETS = {
    "identifier",
    "property_identifier",
}

TYPESCRIPT_TARGETS = JAVASCRIPT_TARGETS | {
    "type_identifier",
}

LANGUAGE_TARGETS: dict[str, set[str]] = {
    "python": PYTHON_TARGETS,
    "javascript": JAVASCRIPT_TARGETS,
    "typescript": TYPESCRIPT_TARGETS,
}

# Parent node types where we DO want to anonymize the child identifier
ANONYMIZABLE_PARENTS = {
    # Python
    "class_definition",
    "function_definition",
    "assignment",
    "augmented_assignment",
    "for_statement",
    "with_clause",
    "as_pattern",
    "keyword_argument",
    "default_parameter",
    "typed_parameter",
    "typed_default_parameter",
    "parameter",
    "attribute",
    "call",
    # JavaScript / TypeScript
    "class_declaration",
    "function_declaration",
    "method_definition",
    "variable_declarator",
    "assignment_expression",
    "member_expression",
    "call_expression",
    "property_identifier",
    "pair",
    "formal_parameters",
}

# Identifiers to NEVER anonymize (builtins, keywords, common stdlib)
PYTHON_BUILTINS = {
    # Keywords & builtins
    "self", "cls", "None", "True", "False", "print", "len", "range",
    "int", "str", "float", "bool", "list", "dict", "set", "tuple",
    "type", "isinstance", "issubclass", "super", "property",
    "staticmethod", "classmethod", "abstractmethod",
    "Exception", "ValueError", "TypeError", "KeyError", "RuntimeError",
    "AttributeError", "IndexError", "StopIteration", "NotImplementedError",
    "OSError", "IOError", "FileNotFoundError", "ImportError",
    "return", "yield", "pass", "break", "continue", "raise",
    "if", "else", "elif", "for", "while", "with", "as", "try",
    "except", "finally", "import", "from", "class", "def", "lambda",
    "and", "or", "not", "in", "is", "del", "global", "nonlocal",
    "assert", "async", "await",
    # Common stdlib
    "os", "sys", "re", "json", "logging", "datetime", "pathlib",
    "typing", "dataclasses", "abc", "collections", "functools",
    "itertools", "math", "hashlib", "uuid", "copy", "io",
    "subprocess", "threading", "asyncio", "contextlib",
    # Common type hints
    "Any", "Optional", "Union", "List", "Dict", "Set", "Tuple",
    "Callable", "Iterator", "Generator", "Coroutine", "Awaitable",
    "Sequence", "Mapping", "Iterable",
    # Testing
    "pytest", "unittest", "mock", "patch",
    # Common identifiers that don't leak business logic
    "main", "init", "setup", "teardown", "run", "start", "stop",
    "get", "set", "add", "remove", "delete", "update", "create",
    "read", "write", "open", "close", "send", "receive",
    "name", "value", "key", "item", "data", "result", "response",
    "request", "error", "message", "status", "code", "text",
    "args", "kwargs", "options", "config", "settings",
    "i", "j", "k", "x", "y", "z", "n", "v", "e", "f", "p", "q",
    "_", "__", "___",
}

JS_BUILTINS = {
    "console", "log", "error", "warn", "info", "debug",
    "document", "window", "global", "globalThis", "process",
    "require", "module", "exports", "import", "export", "default",
    "function", "class", "const", "let", "var", "new", "this",
    "return", "if", "else", "for", "while", "do", "switch", "case",
    "break", "continue", "try", "catch", "finally", "throw",
    "async", "await", "yield", "typeof", "instanceof", "void",
    "null", "undefined", "true", "false", "NaN", "Infinity",
    "Array", "Object", "String", "Number", "Boolean", "Symbol",
    "Map", "Set", "WeakMap", "WeakSet", "Promise", "Proxy",
    "Error", "TypeError", "RangeError", "ReferenceError",
    "JSON", "Math", "Date", "RegExp", "parseInt", "parseFloat",
    "setTimeout", "setInterval", "clearTimeout", "clearInterval",
    "fetch", "Request", "Response", "Headers", "URL",
    "Buffer", "Stream", "EventEmitter",
    "describe", "it", "test", "expect", "jest", "beforeEach", "afterEach",
    "length", "push", "pop", "shift", "map", "filter", "reduce",
    "forEach", "find", "includes", "indexOf", "slice", "splice",
    "keys", "values", "entries", "assign", "freeze", "create",
    "then", "catch", "resolve", "reject", "all", "race",
    "prototype", "constructor", "__proto__",
    "name", "value", "key", "data", "result", "message",
    "i", "j", "k", "x", "y", "z", "n", "e", "err", "cb", "fn",
    "_", "__",
}

LANGUAGE_BUILTINS: dict[str, set[str]] = {
    "python": PYTHON_BUILTINS,
    "javascript": JS_BUILTINS,
    "typescript": JS_BUILTINS | {"interface", "type", "enum", "namespace", "declare", "readonly"},
}


# ---------------------------------------------------------------------------
# AST Anonymizer
# ---------------------------------------------------------------------------

@dataclass
class ASTAnonymizer:
    """Anonymize identifiers in source code using tree-sitter AST parsing.

    Replaces class names, function names, and variable names that could
    reveal business logic with generic placeholders while preserving:
    - Code structure and logic
    - Built-in and stdlib identifiers
    - Import paths (module names kept as-is for functional correctness)
    """

    language: str = "python"
    _mapping: dict[str, str] = field(default_factory=dict)
    _reverse: dict[str, str] = field(default_factory=dict)
    _counters: dict[str, int] = field(default_factory=dict)

    def anonymize(self, code: str) -> tuple[str, list[AnonymizationMapping]]:
        """Parse code and anonymize business-logic identifiers.

        Returns (anonymized_code, mappings_for_rehydration).
        """
        try:
            import tree_sitter
        except ImportError:
            raise ImportError(
                "AST anonymization requires tree-sitter. "
                "Install with: pip install prollama[ast]"
            )

        parser = tree_sitter.Parser()
        ts_language = self._get_language()
        parser.language = ts_language

        code_bytes = code.encode("utf-8")
        tree = parser.parse(code_bytes)
        root = tree.root_node

        # Collect all identifiers to anonymize — pass BYTES for correct position lookups
        replacements: list[tuple[int, int, str, str]] = []  # (start_byte, end_byte, original, replacement)
        self._walk_tree(root, code_bytes, replacements)

        # Deduplicate by (start, end) position — tree walk may visit nodes multiple times
        seen: set[tuple[int, int]] = set()
        unique: list[tuple[int, int, str, str]] = []
        for r in replacements:
            key = (r[0], r[1])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        # Sort by position descending so replacements don't shift offsets
        unique.sort(key=lambda r: r[0], reverse=True)

        # Apply replacements on bytes
        for start, end, original, replacement in unique:
            code_bytes = code_bytes[:start] + replacement.encode("utf-8") + code_bytes[end:]

        anonymized = code_bytes.decode("utf-8")

        # Build mapping list
        mappings = [
            AnonymizationMapping(
                original=orig,
                replacement=repl,
                category="AST_IDENT",
            )
            for orig, repl in self._mapping.items()
        ]

        return anonymized, mappings

    def rehydrate(self, code: str, mappings: list[AnonymizationMapping]) -> str:
        """Restore original identifiers from anonymized code."""
        result = code
        # Sort by replacement length descending to avoid partial matches
        sorted_mappings = sorted(mappings, key=lambda m: len(m.replacement), reverse=True)
        for m in sorted_mappings:
            result = result.replace(m.replacement, m.original)
        return result

    def reset(self) -> None:
        """Clear all mappings and counters."""
        self._mapping.clear()
        self._reverse.clear()
        self._counters.clear()

    def detect_secrets(self, code: str) -> list[str]:
        """Detect potential secrets in code (API keys, passwords, tokens).

        Returns a list of secret values found in the code.
        """
        import re

        secrets = []
        lines = code.split('\n')

        # Pattern for potential secrets
        patterns = [
            (r'(?:api[_-]?key|apikey|api[_-]?secret)\s*[=:]\s*["\']([^"\']+)["\']', 'api_key'),
            (r'(?:password|passwd|pwd)\s*[=:]\s*["\']([^"\']+)["\']', 'password'),
            (r'(?:token|auth[_-]?token)\s*[=:]\s*["\']([^"\']+)["\']', 'token'),
            (r'sk-[a-zA-Z0-9]{48}', 'openai_key'),  # OpenAI key pattern
            (r'gh[pousr]_[A-Za-z0-9_]{36,}', 'github_token'),  # GitHub token
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern, secret_type in patterns:
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    value = match.group(1) if match.groups() else match.group(0)
                    secrets.append(value)

        return secrets

    # -- internals ----------------------------------------------------------

    def _get_language(self):
        """Load the tree-sitter language grammar."""
        import tree_sitter

        if self.language == "python":
            import tree_sitter_python
            return tree_sitter.Language(tree_sitter_python.language())
        elif self.language in ("javascript", "js"):
            import tree_sitter_javascript
            return tree_sitter.Language(tree_sitter_javascript.language())
        else:
            raise ValueError(
                f"Unsupported language: {self.language}. "
                f"Supported: python, javascript"
            )

    def _walk_tree(
        self,
        node,
        source: bytes,
        replacements: list[tuple[int, int, str, str]],
    ) -> None:
        """Recursively walk AST and collect identifier replacements."""
        targets = LANGUAGE_TARGETS.get(self.language, PYTHON_TARGETS)
        builtins = LANGUAGE_BUILTINS.get(self.language, PYTHON_BUILTINS)

        if node.type in targets:
            text = source[node.start_byte:node.end_byte].decode("utf-8")

            # Skip if it's a builtin / protected identifier
            if text in builtins:
                return

            # Skip single-character identifiers
            if len(text) <= 1:
                return

            # Skip identifiers that are all uppercase (likely constants defined
            # by frameworks, e.g. MAX_RETRIES — typically non-sensitive)
            # But DO anonymize SCREAMING_CASE names that are long and specific
            # (likely business-specific constants)
            if text.isupper() and len(text) <= 6:
                return

            # Skip dunder methods
            if text.startswith("__") and text.endswith("__"):
                return

            # Skip import targets — we need module names to stay valid
            if self._is_import_context(node):
                return

            # Skip decorator identifiers
            if self._is_decorator_context(node):
                return

            # Get or create replacement
            replacement = self._get_replacement(text)
            replacements.append((node.start_byte, node.end_byte, text, replacement))

        # Recurse into children
        for child in node.children:
            self._walk_tree(child, source, replacements)

    def _is_import_context(self, node) -> bool:
        """Check if this identifier is part of an import statement."""
        parent = node.parent
        while parent is not None:
            if parent.type in (
                "import_statement", "import_from_statement",
                "import_declaration", "import_specifier",
                "dotted_name",  # Python: from foo.bar import baz
            ):
                return True
            parent = parent.parent
        return False

    def _is_decorator_context(self, node) -> bool:
        """Check if this identifier is part of a decorator."""
        parent = node.parent
        while parent is not None:
            if parent.type == "decorator":
                return True
            parent = parent.parent
        return False

    def _get_replacement(self, identifier: str) -> str:
        """Get a consistent replacement for an identifier.

        Uses naming convention hints to generate appropriate replacements:
        - PascalCase → Class_NNN
        - snake_case → var_NNN
        - camelCase → func_NNN
        - UPPER_CASE → CONST_NNN
        """
        if identifier in self._mapping:
            return self._mapping[identifier]

        category = self._classify_identifier(identifier)
        count = self._counters.get(category, 0) + 1
        self._counters[category] = count
        replacement = f"{category}_{count:03d}"

        self._mapping[identifier] = replacement
        self._reverse[replacement] = identifier
        return replacement

    @staticmethod
    def _classify_identifier(name: str) -> str:
        """Classify identifier by naming convention."""
        if name.isupper() or (name.upper() == name and "_" in name):
            return "CONST"
        if name[0].isupper() and not name.isupper():
            return "Class"
        if "_" in name:
            return "var"
        # camelCase
        if any(c.isupper() for c in name[1:]):
            return "func"
        return "var"
