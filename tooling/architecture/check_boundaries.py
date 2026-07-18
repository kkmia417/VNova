"""Enforce symbol-level safety boundaries that import graphs cannot express."""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path
from typing import Any, NoReturn

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SAFETY_ROOT = (REPOSITORY_ROOT / "packages" / "safety").resolve()
SCAN_ROOTS = (
    REPOSITORY_ROOT / "apps",
    REPOSITORY_ROOT / "packages",
    REPOSITORY_ROOT / "tooling",
)
IGNORED_PARTS = frozenset({".venv", "dist", "node_modules", "__pycache__"})
PYTHON_SOURCE_SUFFIXES = frozenset({".py", ".pyi"})
TYPING_MODULE_NAMES = frozenset({"typing", "typing_extensions"})
DIRECT_ANNOTATION_WRAPPERS = frozenset(
    {"Annotated", "ClassVar", "Final", "NotRequired", "Required"}
)
APPROVED_DIRECT = "direct"
APPROVED_CONTAINER = "container"
APPROVED_OPTIONAL_DIRECT = "optional-direct"
APPROVED_OPTIONAL_CONTAINER = "optional-container"
FORBIDDEN_SPEECH_TASK_FIELDS = frozenset({"content", "rawtext", "ssml", "text"})
ALLOWED_SPEECH_TASK_FIELDS = frozenset(
    {
        "approved_response_id",
        "audience",
        "integrity_digest",
        "issued_at",
        "issuer",
        "key_id",
        "media_artifact_id",
        "not_after",
        "not_before",
        "ordering_identity",
        "queue_sequence",
        "safety_decision_id",
        "schema_version",
        "session_epoch",
        "speech_task_id",
        "stream_session_id",
        "token_id",
    }
)
FORBIDDEN_SPEECH_TASK_SCHEMA_KEYWORDS = frozenset(
    {
        "$dynamicRef",
        "$recursiveRef",
        "$ref",
        "allOf",
        "anyOf",
        "dependentSchemas",
        "dependencies",
        "else",
        "if",
        "not",
        "oneOf",
        "patternProperties",
        "propertyNames",
        "then",
    }
)
ALLOWED_SPEECH_TASK_VALUE_TYPES = frozenset({"integer", "string"})
UUID_SPEECH_TASK_FIELDS = frozenset(
    {
        "approved_response_id",
        "media_artifact_id",
        "safety_decision_id",
        "speech_task_id",
        "stream_session_id",
        "token_id",
    }
)
ALLOWED_SPEECH_TASK_PROPERTY_SCHEMA_KEYWORDS = frozenset(
    {
        "$comment",
        "const",
        "default",
        "deprecated",
        "description",
        "enum",
        "examples",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "format",
        "maxLength",
        "maximum",
        "minLength",
        "minimum",
        "multipleOf",
        "pattern",
        "readOnly",
        "title",
        "type",
        "writeOnly",
    }
)
IMPORT_FROM_LIST_POSITION = 3
GETATTR_ATTRIBUTE_ARGUMENT_POSITION = 1
PROTECTED_SAFETY_MODULE_PARTS = frozenset({"_mint", "internal", "private"})
DYNAMIC_LOADER_IMPORTLIB_MEMBERS = frozenset({"import_module", "machinery", "util"})
DYNAMIC_LOADER_ATTRIBUTE_NAMES = frozenset(
    {"__import__", "create_module", "exec_module", "import_module", "load_module"}
)


@dataclass(frozen=True)
class BoundaryViolation:
    path: Path
    line: int
    message: str

    def render(self) -> str:
        relative = self.path.relative_to(REPOSITORY_ROOT)
        return f"{relative}:{self.line}: {self.message}"


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False
    return True


def _python_paths() -> list[Path]:
    paths: set[Path] = set()
    for scan_root in SCAN_ROOTS:
        if not scan_root.exists():
            continue
        for suffix in PYTHON_SOURCE_SUFFIXES:
            paths.update(
                path
                for path in scan_root.rglob(f"*{suffix}")
                if not IGNORED_PARTS.intersection(path.parts)
            )
    return sorted(paths)


def _call_name(node: ast.Call) -> str | None:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return None


def _literal_string(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _is_protected_safety_module_reference(value: str) -> bool:
    relative = value.startswith(".")
    parts = tuple(part.casefold() for part in value.lstrip(".").split(".") if part)
    return (
        bool(parts)
        and (relative or parts[0] == "vnova_safety")
        and bool(PROTECTED_SAFETY_MODULE_PARTS.intersection(parts))
    )


def _imports_protected_mint_dynamically(
    node: ast.Call,
    importlib_aliases: set[str],
    import_module_aliases: set[str],
) -> bool:
    function = node.func
    is_builtin_import = isinstance(function, ast.Name) and function.id == "__import__"
    is_import_module = (
        isinstance(function, ast.Name) and function.id in import_module_aliases
    ) or (
        isinstance(function, ast.Attribute)
        and function.attr == "import_module"
        and isinstance(function.value, ast.Name)
        and function.value.id in importlib_aliases
    )
    if not is_builtin_import and not is_import_module:
        return False
    keyword_target = next(
        (_literal_string(keyword.value) for keyword in node.keywords if keyword.arg == "name"),
        None,
    )
    target = (_literal_string(node.args[0]) if node.args else None) or keyword_target
    if target is None:
        return False
    target_casefold = target.casefold()
    if _is_protected_safety_module_reference(target) and not target.startswith("."):
        return True
    if is_import_module and _is_protected_safety_module_reference(target):
        keyword_package = next(
            (
                _literal_string(keyword.value)
                for keyword in node.keywords
                if keyword.arg == "package"
            ),
            None,
        )
        package = keyword_package or (_literal_string(node.args[1]) if len(node.args) > 1 else None)
        package_casefold = package.casefold() if package is not None else None
        return package_casefold == "vnova_safety" or (
            package_casefold is not None and package_casefold.startswith("vnova_safety.")
        )
    if is_builtin_import and (
        target_casefold == "vnova_safety" or target_casefold.startswith("vnova_safety.")
    ):
        keyword_fromlist = next(
            (keyword.value for keyword in node.keywords if keyword.arg == "fromlist"),
            None,
        )
        fromlist = keyword_fromlist or (
            node.args[IMPORT_FROM_LIST_POSITION]
            if len(node.args) > IMPORT_FROM_LIST_POSITION
            else None
        )
        if isinstance(fromlist, (ast.List, ast.Tuple, ast.Set)):
            return any(
                any(part.casefold() in PROTECTED_SAFETY_MODULE_PARTS for part in literal.split("."))
                for item in fromlist.elts
                if (literal := _literal_string(item)) is not None
            )
    return False


def _references_approved_response(node: ast.AST, aliases: set[str]) -> bool:
    return any(
        (isinstance(candidate, ast.Name) and candidate.id in aliases)
        or (isinstance(candidate, ast.Attribute) and candidate.attr == "ApprovedResponse")
        for candidate in ast.walk(node)
    )


def _parse_forward_annotation(node: ast.AST) -> ast.AST | None:
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return None
    try:
        return ast.parse(node.value, mode="eval").body
    except SyntaxError:
        return None


def _annotation_references_name(node: ast.AST, names: set[str]) -> bool:
    parsed = _parse_forward_annotation(node)
    if parsed is not None:
        references_name = _annotation_references_name(parsed, names)
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        references_name = False
    elif isinstance(node, ast.Name):
        references_name = node.id in names
    elif isinstance(node, ast.Attribute):
        references_name = node.attr in names or _annotation_references_name(node.value, names)
    elif isinstance(node, ast.Subscript):
        annotation_name = (_qualified_name(node.value) or "").rsplit(".", maxsplit=1)[-1]
        elements = _annotation_elements(node.slice)
        if annotation_name == "Literal":
            references_name = False
        elif annotation_name == "Annotated":
            references_name = bool(elements) and _annotation_references_name(elements[0], names)
        else:
            references_name = any(
                _annotation_references_name(child, names) for child in ast.iter_child_nodes(node)
            )
    else:
        references_name = any(
            _annotation_references_name(child, names) for child in ast.iter_child_nodes(node)
        )
    return references_name


def _annotation_references_approved_response(node: ast.AST, aliases: set[str]) -> bool:
    return _annotation_references_name(node, aliases)


def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if not isinstance(node, ast.Attribute):
        return None
    parent = _qualified_name(node.value)
    return f"{parent}.{node.attr}" if parent is not None else node.attr


def _annotation_is_none(node: ast.AST) -> bool:
    parsed = _parse_forward_annotation(node)
    if parsed is not None:
        return _annotation_is_none(parsed)
    return (isinstance(node, ast.Constant) and node.value is None) or (
        isinstance(node, ast.Name) and node.id == "None"
    )


def _annotation_elements(node: ast.AST) -> tuple[ast.AST, ...]:
    return tuple(node.elts) if isinstance(node, ast.Tuple) else (node,)


def _union_annotation_kind(
    members: tuple[ast.AST, ...],
    aliases: set[str],
) -> str | None:
    allows_none = any(_annotation_is_none(member) for member in members)
    member_kinds = [
        kind
        for member in members
        if not _annotation_is_none(member)
        and (kind := _approved_annotation_kind(member, aliases)) is not None
    ]
    if not member_kinds:
        return None
    direct_only = all(kind in {APPROVED_DIRECT, APPROVED_OPTIONAL_DIRECT} for kind in member_kinds)
    if direct_only:
        return APPROVED_OPTIONAL_DIRECT if allows_none else APPROVED_DIRECT
    return APPROVED_OPTIONAL_CONTAINER if allows_none else APPROVED_CONTAINER


def _is_direct_approved_annotation(node: ast.AST, aliases: set[str]) -> bool:
    return (isinstance(node, ast.Name) and node.id in aliases) or (
        isinstance(node, ast.Attribute) and node.attr in aliases
    )


def _approved_subscript_annotation_kind(
    node: ast.Subscript,
    aliases: set[str],
) -> str | None:
    annotation_name = (_qualified_name(node.value) or "").rsplit(".", maxsplit=1)[-1]
    elements = _annotation_elements(node.slice)
    if annotation_name in DIRECT_ANNOTATION_WRAPPERS and elements:
        return _approved_annotation_kind(elements[0], aliases)
    if annotation_name == "Optional" and elements:
        nested = _approved_annotation_kind(elements[0], aliases)
        if nested in {APPROVED_DIRECT, APPROVED_OPTIONAL_DIRECT}:
            return APPROVED_OPTIONAL_DIRECT
        return APPROVED_OPTIONAL_CONTAINER if nested is not None else None
    if annotation_name == "Union":
        return _union_annotation_kind(elements, aliases)
    if _annotation_references_approved_response(node, aliases):
        return APPROVED_CONTAINER
    return None


def _approved_annotation_kind(node: ast.AST, aliases: set[str]) -> str | None:
    parsed = _parse_forward_annotation(node)
    if parsed is not None:
        kind = _approved_annotation_kind(parsed, aliases)
    elif _is_direct_approved_annotation(node, aliases):
        kind = APPROVED_DIRECT
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        kind = _union_annotation_kind((node.left, node.right), aliases)
    elif isinstance(node, ast.Subscript):
        kind = _approved_subscript_annotation_kind(node, aliases)
    elif _annotation_references_approved_response(node, aliases):
        kind = APPROVED_CONTAINER
    else:
        kind = None
    return kind


def _annotation_references_any(node: ast.AST) -> bool:
    return _annotation_references_name(node, {"Any"})


def _bound_target_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, ast.Starred):
        return _bound_target_names(node.value)
    if isinstance(node, (ast.List, ast.Tuple)):
        return {name for child in node.elts for name in _bound_target_names(child)}
    return set()


def _discover_assignment_aliases(tree: ast.AST, aliases: set[str]) -> bool:
    changed = False
    for node in ast.walk(tree):
        targets: list[ast.expr]
        if isinstance(node, ast.TypeAlias):
            if not _references_approved_response(node.value, aliases):
                continue
            targets = [node.name]
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if value is None or not _references_approved_response(value, aliases):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id not in aliases:
                aliases.add(target.id)
                changed = True
    return changed


def _discover_subclass_aliases(tree: ast.AST, aliases: set[str]) -> bool:
    changed = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ClassDef)
            and any(_references_approved_response(base, aliases) for base in node.bases)
            and node.name not in aliases
        ):
            aliases.add(node.name)
            changed = True
    return changed


def _approved_response_aliases(tree: ast.AST) -> set[str]:
    aliases = {"ApprovedResponse"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            aliases.update(
                imported.asname or imported.name
                for imported in node.names
                if imported.name == "ApprovedResponse"
            )

    changed = True
    while changed:
        changed = _discover_assignment_aliases(tree, aliases)
        changed = _discover_subclass_aliases(tree, aliases) or changed
    return aliases


def _dynamic_import_aliases(tree: ast.AST) -> tuple[set[str], set[str]]:
    importlib_aliases = {"importlib"}
    import_module_aliases: set[str] = set()
    for candidate in ast.walk(tree):
        if isinstance(candidate, ast.Import):
            importlib_aliases.update(
                imported.asname or imported.name
                for imported in candidate.names
                if imported.name == "importlib"
            )
        elif isinstance(candidate, ast.ImportFrom) and candidate.module == "importlib":
            import_module_aliases.update(
                imported.asname or imported.name
                for imported in candidate.names
                if imported.name == "import_module"
            )
    changed = True
    while changed:
        changed = False
        for candidate in ast.walk(tree):
            if not isinstance(candidate, (ast.Assign, ast.AnnAssign)) or candidate.value is None:
                continue
            value = candidate.value
            aliases_import_module = (
                isinstance(value, ast.Name) and value.id in import_module_aliases
            ) or (
                isinstance(value, ast.Attribute)
                and value.attr == "import_module"
                and isinstance(value.value, ast.Name)
                and value.value.id in importlib_aliases
            )
            if not aliases_import_module:
                continue
            targets = candidate.targets if isinstance(candidate, ast.Assign) else [candidate.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id not in import_module_aliases:
                    import_module_aliases.add(target.id)
                    changed = True
    return importlib_aliases, import_module_aliases


def _is_private_safety_source(path: Path) -> bool:
    if not _is_under(path, SAFETY_ROOT):
        return False
    relative_parts = path.resolve().relative_to(SAFETY_ROOT).parts
    return any(
        Path(part).stem.casefold() in PROTECTED_SAFETY_MODULE_PARTS for part in relative_parts
    )


def _imports_protected_mint_statically(node: ast.AST) -> bool:
    if isinstance(node, ast.Import):
        return any(_is_protected_safety_module_reference(imported.name) for imported in node.names)
    if not isinstance(node, ast.ImportFrom):
        return False
    module = node.module or ""
    imported_protected_name = any(
        imported.name.casefold() in PROTECTED_SAFETY_MODULE_PARTS for imported in node.names
    )
    module_reference = f"{'.' * node.level}{module}" if node.level > 0 else module
    module_casefold = module.casefold()
    return _is_protected_safety_module_reference(module_reference) or (
        imported_protected_name
        and (
            module_casefold == "vnova_safety"
            or module_casefold.startswith("vnova_safety.")
            or node.level > 0
        )
    )


def _protected_import_local_names(node: ast.AST) -> tuple[set[str], set[str]]:
    if not _imports_protected_mint_statically(node):
        return set(), set()
    aliases: set[str] = set()
    mint_aliases: set[str] = set()
    if isinstance(node, ast.Import):
        for imported in node.names:
            if not _is_protected_safety_module_reference(imported.name):
                continue
            local_name = imported.asname or imported.name.split(".")[0]
            aliases.add(local_name)
            if "_mint" in (part.casefold() for part in imported.name.split(".")):
                mint_aliases.add(local_name)
        return aliases, mint_aliases
    if not isinstance(node, ast.ImportFrom):
        return aliases, mint_aliases
    module = node.module or ""
    module_reference = f"{'.' * node.level}{module}" if node.level > 0 else module
    module_is_private = _is_protected_safety_module_reference(module_reference)
    module_is_mint = "_mint" in (
        part.casefold() for part in module_reference.lstrip(".").split(".")
    )
    for imported in node.names:
        imported_name_casefold = imported.name.casefold()
        if not module_is_private and imported_name_casefold not in PROTECTED_SAFETY_MODULE_PARTS:
            continue
        local_name = imported.asname or imported.name
        aliases.add(local_name)
        if module_is_mint or imported_name_casefold == "_mint":
            mint_aliases.add(local_name)
    return aliases, mint_aliases


def _private_safety_import_aliases(
    tree: ast.Module,
) -> tuple[set[str], set[str], list[tuple[ast.AST, set[str]]]]:
    aliases: set[str] = set()
    mint_aliases: set[str] = set()
    imports: list[tuple[ast.AST, set[str]]] = []
    for node in tree.body:
        local_names, local_mint_names = _protected_import_local_names(node)
        if not local_names:
            continue
        aliases.update(local_names)
        mint_aliases.update(local_mint_names)
        imports.append((node, local_names))
    return aliases, mint_aliases, imports


def _private_alias_root(node: ast.AST, aliases: set[str]) -> str | None:
    current = node
    while isinstance(current, (ast.Attribute, ast.Subscript)):
        current = current.value
    return current.id if isinstance(current, ast.Name) and current.id in aliases else None


def _expression_exposes_private_import(
    node: ast.AST,
    aliases: set[str],
    mint_aliases: set[str],
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in aliases
    if isinstance(node, ast.Call):
        root_alias = _private_alias_root(node.func, aliases)
        if root_alias is not None and root_alias not in mint_aliases:
            return True
        return any(
            _expression_exposes_private_import(argument, aliases, mint_aliases)
            for argument in node.args
        ) or any(
            _expression_exposes_private_import(keyword.value, aliases, mint_aliases)
            for keyword in node.keywords
        )
    children: tuple[ast.AST, ...] = ()
    if isinstance(node, (ast.Attribute, ast.Subscript, ast.Await, ast.Starred, ast.NamedExpr)):
        children = (node.value,)
    elif isinstance(node, ast.UnaryOp):
        children = (node.operand,)
    if isinstance(node, ast.Dict):
        children = tuple(child for child in (*node.keys, *node.values) if child is not None)
    elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        children = tuple(node.elts)
    elif isinstance(node, ast.BoolOp):
        children = tuple(node.values)
    elif isinstance(node, ast.IfExp):
        children = (node.body, node.orelse)
    elif isinstance(node, ast.Lambda):
        children = (node.body,)
    return any(
        _expression_exposes_private_import(child, aliases, mint_aliases) for child in children
    )


def _assignment_public_names(node: ast.Assign | ast.AnnAssign) -> set[str]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return {
        candidate.id
        for target in targets
        for candidate in ast.walk(target)
        if isinstance(candidate, ast.Name) and not candidate.id.startswith("_")
    }


def _all_exports_private_alias(node: ast.Assign | ast.AnnAssign, aliases: set[str]) -> bool:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
        return False
    value = node.value
    if not isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        return False
    return any(_literal_string(item) in aliases for item in value.elts)


def _node_returns_private_import(
    node: ast.AST,
    aliases: set[str],
    mint_aliases: set[str],
) -> bool:
    return any(
        isinstance(candidate, ast.Return)
        and candidate.value is not None
        and _expression_exposes_private_import(candidate.value, aliases, mint_aliases)
        for candidate in ast.walk(node)
    )


def _public_safety_surface_violations(path: Path, tree: ast.Module) -> list[BoundaryViolation]:
    if not _is_under(path, SAFETY_ROOT) or _is_private_safety_source(path):
        return []
    aliases, mint_aliases, imports = _private_safety_import_aliases(tree)
    violations = [
        BoundaryViolation(
            path,
            getattr(node, "lineno", 1),
            "Imports from private safety modules must use underscore-prefixed local aliases",
        )
        for node, local_names in imports
        if any(not local_name.startswith("_") for local_name in local_names)
    ]
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            if _all_exports_private_alias(node, aliases) or (
                _assignment_public_names(node)
                and _expression_exposes_private_import(node.value, aliases, mint_aliases)
            ):
                violations.append(
                    BoundaryViolation(
                        path,
                        node.lineno,
                        "A private safety capability cannot be assigned to a public module name",
                    )
                )
        elif (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
            and _node_returns_private_import(node, aliases, mint_aliases)
        ):
            violations.append(
                BoundaryViolation(
                    path,
                    node.lineno,
                    "A public safety function cannot return a private safety capability",
                )
            )
        elif (
            isinstance(node, ast.ClassDef)
            and not node.name.startswith("_")
            and _node_returns_private_import(node, aliases, mint_aliases)
        ):
            violations.append(
                BoundaryViolation(
                    path,
                    node.lineno,
                    "A public safety class cannot return a private safety capability",
                )
            )
    return violations


def _is_dynamic_loader_import(node: ast.AST) -> bool:
    if isinstance(node, ast.Import):
        return any(
            imported.name.casefold() == "importlib"
            or imported.name.casefold().startswith("importlib.")
            for imported in node.names
        )
    if not isinstance(node, ast.ImportFrom):
        return False
    module = (node.module or "").casefold()
    imported_names = {imported.name.casefold() for imported in node.names}
    return (
        (module == "builtins" and "__import__" in imported_names)
        or (
            module == "importlib"
            and bool(imported_names.intersection(DYNAMIC_LOADER_IMPORTLIB_MEMBERS))
        )
        or module.startswith(("importlib.machinery", "importlib.util"))
    )


def _is_dynamic_loader_surface(node: ast.AST) -> bool:
    is_surface = _is_dynamic_loader_import(node)
    if isinstance(node, ast.Name):
        is_surface = is_surface or (isinstance(node.ctx, ast.Load) and node.id == "__import__")
    elif isinstance(node, ast.Attribute):
        is_surface = is_surface or node.attr.casefold() in DYNAMIC_LOADER_ATTRIBUTE_NAMES
    elif isinstance(node, ast.Subscript):
        key = _literal_string(node.slice)
        is_surface = is_surface or (
            key is not None and key.casefold() in DYNAMIC_LOADER_ATTRIBUTE_NAMES
        )
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) > GETATTR_ATTRIBUTE_ARGUMENT_POSITION
    ):
        attribute_name = _literal_string(node.args[GETATTR_ATTRIBUTE_ARGUMENT_POSITION])
        is_surface = is_surface or (
            attribute_name is not None
            and attribute_name.casefold() in DYNAMIC_LOADER_ATTRIBUTE_NAMES
        )
    return is_surface


def _dynamic_loader_surface_violations(
    path: Path,
    tree: ast.Module,
) -> list[BoundaryViolation]:
    return [
        BoundaryViolation(
            path,
            getattr(node, "lineno", 1),
            "Dynamic module-loading primitives are forbidden in governed source; "
            "introduce an ADR-reviewed allowlist before enabling one",
        )
        for node in ast.walk(tree)
        if _is_dynamic_loader_surface(node)
    ]


def _protected_mint_import_violations(
    node: ast.AST,
    path: Path,
    inside_safety: bool,
    importlib_aliases: set[str],
    import_module_aliases: set[str],
) -> list[BoundaryViolation]:
    if inside_safety and _is_private_safety_source(path):
        return []
    if inside_safety:
        forbidden_private_import = _imports_protected_mint_statically(node) or (
            isinstance(node, ast.Call)
            and _imports_protected_mint_dynamically(
                node,
                importlib_aliases,
                import_module_aliases,
            )
        )
        if not forbidden_private_import:
            return []
        return [
            BoundaryViolation(
                path,
                getattr(node, "lineno", 1),
                "A public safety module cannot import a private safety module",
            )
        ]
    forbidden = _imports_protected_mint_statically(node) and not (
        isinstance(node, ast.ImportFrom) and node.level > 0
    )
    if isinstance(node, ast.Call):
        forbidden = forbidden or _imports_protected_mint_dynamically(
            node,
            importlib_aliases,
            import_module_aliases,
        )
    if not forbidden:
        return []
    return [
        BoundaryViolation(
            path,
            getattr(node, "lineno", 1),
            "The protected safety mint module cannot be imported here",
        )
    ]


def _typing_cast_aliases(tree: ast.Module) -> tuple[set[str], set[str]]:
    module_aliases = {"typing"}
    cast_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            module_aliases.update(
                imported.asname or imported.name
                for imported in node.names
                if imported.name in TYPING_MODULE_NAMES
            )
        elif isinstance(node, ast.ImportFrom) and node.module in TYPING_MODULE_NAMES:
            cast_aliases.update(
                imported.asname or imported.name
                for imported in node.names
                if imported.name == "cast"
            )

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            target_names = {name for target in targets for name in _bound_target_names(target)}
            if isinstance(node.value, ast.Name) and node.value.id in module_aliases:
                additions = target_names - module_aliases
                module_aliases.update(additions)
                changed = bool(additions) or changed
            if _is_typing_cast_reference(node.value, module_aliases, cast_aliases):
                additions = target_names - cast_aliases
                cast_aliases.update(additions)
                changed = bool(additions) or changed
    return module_aliases, cast_aliases


def _is_typing_cast_reference(
    node: ast.AST,
    module_aliases: set[str],
    cast_aliases: set[str],
) -> bool:
    return (isinstance(node, ast.Name) and node.id in cast_aliases) or (
        isinstance(node, ast.Attribute)
        and node.attr == "cast"
        and isinstance(node.value, ast.Name)
        and node.value.id in module_aliases
    )


def _is_ellipsis(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is Ellipsis


def _is_ambient_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    path: Path,
) -> bool:
    if path.suffix == ".pyi":
        return True
    return len(node.body) == 1 and (
        isinstance(node.body[0], ast.Pass)
        or (isinstance(node.body[0], ast.Expr) and _is_ellipsis(node.body[0].value))
    )


def _external_approved_response_declaration_violations(
    path: Path,
    tree: ast.Module,
    aliases: set[str],
) -> list[BoundaryViolation]:
    module_aliases, cast_aliases = _typing_cast_aliases(tree)
    violations: list[BoundaryViolation] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None and _annotation_references_approved_response(
                node.returns, aliases
            ):
                message = (
                    "Ambient ApprovedResponse producers are forbidden outside packages/safety"
                    if _is_ambient_function(node, path)
                    else "ApprovedResponse producer functions are forbidden outside packages/safety"
                )
                violations.append(BoundaryViolation(path, node.returns.lineno, message))
        elif isinstance(node, ast.AnnAssign):
            if _annotation_references_approved_response(node.annotation, aliases) and (
                node.value is None or _is_ellipsis(node.value) or path.suffix == ".pyi"
            ):
                violations.append(
                    BoundaryViolation(
                        path,
                        node.annotation.lineno,
                        "Ambient ApprovedResponse values are forbidden outside packages/safety",
                    )
                )
        elif isinstance(node, ast.Call) and _is_typing_cast_reference(
            node.func, module_aliases, cast_aliases
        ):
            if node.args and _annotation_references_approved_response(node.args[0], aliases):
                violations.append(
                    BoundaryViolation(
                        path,
                        node.lineno,
                        "ApprovedResponse casts are forbidden outside packages/safety",
                    )
                )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any("ApprovedResponse" in _bound_target_names(target) for target in targets):
                violations.append(
                    BoundaryViolation(
                        path,
                        node.lineno,
                        "ApprovedResponse may be defined only under packages/safety",
                    )
                )
        elif (
            isinstance(node, ast.TypeAlias)
            and isinstance(node.name, ast.Name)
            and node.name.id == "ApprovedResponse"
        ):
            violations.append(
                BoundaryViolation(
                    path,
                    node.lineno,
                    "ApprovedResponse may be defined only under packages/safety",
                )
            )
    return violations


def _is_safety_module_name(value: str) -> bool:
    normalized = value.casefold()
    return normalized == "vnova_safety" or normalized.startswith("vnova_safety.")


@dataclass
class _ApprovedResponseTrustState:
    direct: set[str] = dataclass_field(default_factory=set)
    containers: set[str] = dataclass_field(default_factory=set)
    safety_modules: set[str] = dataclass_field(default_factory=set)
    safety_values: set[str] = dataclass_field(default_factory=set)

    def clone(self) -> _ApprovedResponseTrustState:
        return _ApprovedResponseTrustState(
            direct=set(self.direct),
            containers=set(self.containers),
            safety_modules=set(self.safety_modules),
            safety_values=set(self.safety_values),
        )

    def retain_common(self, *branches: _ApprovedResponseTrustState) -> None:
        for attribute in ("direct", "containers", "safety_modules", "safety_values"):
            current = getattr(self, attribute)
            if branches:
                current.intersection_update(*(getattr(branch, attribute) for branch in branches))

    def forget(self, names: set[str]) -> None:
        self.direct.difference_update(names)
        self.containers.difference_update(names)
        self.safety_modules.difference_update(names)
        self.safety_values.difference_update(names)


def _expression_root_name(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, (ast.Attribute, ast.Subscript)):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


def _is_safety_owned_expression(node: ast.AST, state: _ApprovedResponseTrustState) -> bool:
    if isinstance(node, ast.Name):
        return node.id in state.safety_values
    if isinstance(node, ast.Attribute):
        return _expression_root_name(node) in state.safety_modules
    if isinstance(node, ast.Call):
        return _is_safety_owned_expression(node.func, state)
    return False


def _has_trusted_direct_origin(node: ast.AST, state: _ApprovedResponseTrustState) -> bool:
    if isinstance(node, ast.Name):
        trusted = node.id in state.direct or node.id in state.safety_values
    elif _is_safety_owned_expression(node, state):
        trusted = True
    elif isinstance(node, (ast.Await, ast.NamedExpr, ast.Starred)):
        trusted = _has_trusted_direct_origin(node.value, state)
    elif isinstance(node, (ast.Attribute, ast.Subscript)):
        trusted = _has_trusted_container_origin(node.value, state)
    elif isinstance(node, ast.IfExp):
        trusted = _has_trusted_direct_origin(node.body, state) and _has_trusted_direct_origin(
            node.orelse, state
        )
    else:
        trusted = False
    return trusted


def _has_trusted_container_origin(node: ast.AST, state: _ApprovedResponseTrustState) -> bool:
    if isinstance(node, ast.Name):
        trusted = node.id in state.containers or node.id in state.safety_values
    elif _is_safety_owned_expression(node, state):
        trusted = True
    elif isinstance(node, (ast.Await, ast.NamedExpr, ast.Starred)):
        trusted = _has_trusted_container_origin(node.value, state)
    elif isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        trusted = all(
            _has_trusted_direct_origin(child, state) or _has_trusted_container_origin(child, state)
            for child in node.elts
        )
    elif isinstance(node, ast.Dict):
        trusted = all(
            _has_trusted_direct_origin(child, state) or _has_trusted_container_origin(child, state)
            for child in node.values
        )
    elif isinstance(node, (ast.Attribute, ast.Subscript)):
        trusted = _has_trusted_container_origin(node.value, state)
    elif isinstance(node, ast.IfExp):
        trusted = _has_trusted_container_origin(node.body, state) and _has_trusted_container_origin(
            node.orelse, state
        )
    else:
        trusted = False
    return trusted


def _has_trusted_optional_direct_origin(
    node: ast.AST,
    state: _ApprovedResponseTrustState,
) -> bool:
    if isinstance(node, ast.Constant) and node.value is None:
        return True
    if isinstance(node, ast.IfExp):
        return _has_trusted_optional_direct_origin(
            node.body, state
        ) and _has_trusted_optional_direct_origin(node.orelse, state)
    return _has_trusted_direct_origin(node, state)


def _has_trusted_optional_container_origin(
    node: ast.AST,
    state: _ApprovedResponseTrustState,
) -> bool:
    if isinstance(node, ast.Constant) and node.value is None:
        return True
    if isinstance(node, ast.IfExp):
        return _has_trusted_optional_container_origin(
            node.body, state
        ) and _has_trusted_optional_container_origin(node.orelse, state)
    return _has_trusted_container_origin(node, state)


def _has_trusted_origin(
    kind: str,
    node: ast.AST,
    state: _ApprovedResponseTrustState,
) -> bool:
    if kind == APPROVED_DIRECT:
        return _has_trusted_direct_origin(node, state)
    if kind == APPROVED_OPTIONAL_DIRECT:
        return _has_trusted_optional_direct_origin(node, state)
    if kind == APPROVED_OPTIONAL_CONTAINER:
        return _has_trusted_optional_container_origin(node, state)
    return _has_trusted_container_origin(node, state)


class _ApprovedResponseFlowAnalyzer:
    def __init__(self, path: Path, aliases: set[str]) -> None:
        self._path = path
        self._aliases = aliases
        self._violations: list[BoundaryViolation] = []

    def analyze(self, tree: ast.Module) -> list[BoundaryViolation]:
        self._visit_block(tree.body, _ApprovedResponseTrustState())
        return self._violations

    def _visit_block(
        self,
        statements: list[ast.stmt],
        state: _ApprovedResponseTrustState,
    ) -> None:
        for statement in statements:
            self._visit_statement(statement, state)

    def _visit_statement(
        self,
        statement: ast.stmt,
        state: _ApprovedResponseTrustState,
    ) -> None:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            self._record_import(statement, state)
            return
        if isinstance(statement, ast.AnnAssign):
            self._record_annotated_assignment(statement, state)
            return
        if isinstance(statement, ast.Assign):
            self._record_assignment(statement, state)
            return
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._visit_function(statement, state)
            return
        if isinstance(statement, ast.ClassDef):
            self._visit_class(statement, state)
            return
        if self._visit_branching_statement(statement, state):
            return
        if isinstance(statement, (ast.AugAssign, ast.Delete)):
            targets = (
                [statement.target] if isinstance(statement, ast.AugAssign) else statement.targets
            )
            state.forget({name for target in targets for name in _bound_target_names(target)})

    def _record_import(
        self,
        statement: ast.Import | ast.ImportFrom,
        state: _ApprovedResponseTrustState,
    ) -> None:
        if isinstance(statement, ast.Import):
            for imported in statement.names:
                local_name = imported.asname or imported.name.split(".", maxsplit=1)[0]
                state.forget({local_name})
                if _is_safety_module_name(imported.name):
                    state.safety_modules.add(local_name)
            return
        for imported in statement.names:
            local_name = imported.asname or imported.name
            state.forget({local_name})
            if (
                statement.level == 0
                and statement.module is not None
                and _is_safety_module_name(statement.module)
                and imported.name != "ApprovedResponse"
            ):
                state.safety_values.add(local_name)

    def _record_annotated_assignment(
        self,
        statement: ast.AnnAssign,
        state: _ApprovedResponseTrustState,
    ) -> None:
        names = _bound_target_names(statement.target)
        kind = _approved_annotation_kind(statement.annotation, self._aliases)
        if kind is None or statement.value is None or _is_ellipsis(statement.value):
            state.forget(names)
            return
        direct_origin = _has_trusted_direct_origin(statement.value, state)
        container_origin = _has_trusted_container_origin(statement.value, state)
        trusted = _has_trusted_origin(kind, statement.value, state)
        safety_owned = _is_safety_owned_expression(statement.value, state)
        state.forget(names)
        if not trusted:
            message = (
                "Untrusted value cannot flow into ApprovedResponse"
                if kind in {APPROVED_DIRECT, APPROVED_OPTIONAL_DIRECT}
                else "Untrusted value cannot flow into an ApprovedResponse container"
            )
            self._violations.append(BoundaryViolation(self._path, statement.value.lineno, message))
            return
        if safety_owned:
            state.safety_values.update(names)
        elif kind == APPROVED_DIRECT or (kind == APPROVED_OPTIONAL_DIRECT and direct_origin):
            state.direct.update(names)
        elif kind == APPROVED_CONTAINER or (
            kind == APPROVED_OPTIONAL_CONTAINER and container_origin
        ):
            state.containers.update(names)

    def _record_assignment(
        self,
        statement: ast.Assign,
        state: _ApprovedResponseTrustState,
    ) -> None:
        names = {name for target in statement.targets for name in _bound_target_names(target)}
        safety_owned = _is_safety_owned_expression(statement.value, state)
        direct = _has_trusted_direct_origin(statement.value, state)
        container = _has_trusted_container_origin(statement.value, state)
        state.forget(names)
        if safety_owned:
            state.safety_values.update(names)
        elif direct:
            state.direct.update(names)
        elif container:
            state.containers.update(names)

    def _visit_function(
        self,
        statement: ast.FunctionDef | ast.AsyncFunctionDef,
        state: _ApprovedResponseTrustState,
    ) -> None:
        state.forget({statement.name})
        child = state.clone()
        positional = (*statement.args.posonlyargs, *statement.args.args, *statement.args.kwonlyargs)
        for argument in positional:
            self._record_parameter(argument, child, container=False)
        if statement.args.vararg is not None:
            self._record_parameter(statement.args.vararg, child, container=True)
        if statement.args.kwarg is not None:
            self._record_parameter(statement.args.kwarg, child, container=True)
        self._visit_block(statement.body, child)

    def _record_parameter(
        self,
        argument: ast.arg,
        state: _ApprovedResponseTrustState,
        *,
        container: bool,
    ) -> None:
        state.forget({argument.arg})
        if argument.annotation is None or _annotation_references_any(argument.annotation):
            return
        kind = _approved_annotation_kind(argument.annotation, self._aliases)
        if kind is None:
            return
        if container or kind in {APPROVED_CONTAINER, APPROVED_OPTIONAL_CONTAINER}:
            state.containers.add(argument.arg)
        else:
            state.direct.add(argument.arg)

    def _visit_class(
        self,
        statement: ast.ClassDef,
        state: _ApprovedResponseTrustState,
    ) -> None:
        state.forget({statement.name})
        self._visit_block(statement.body, state.clone())

    def _visit_branching_statement(
        self,
        statement: ast.stmt,
        state: _ApprovedResponseTrustState,
    ) -> bool:
        if isinstance(statement, ast.If):
            body = state.clone()
            alternative = state.clone()
            self._visit_block(statement.body, body)
            self._visit_block(statement.orelse, alternative)
            state.retain_common(body, alternative)
            handled = True
        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            body = state.clone()
            body.forget(_bound_target_names(statement.target))
            self._visit_block(statement.body, body)
            self._visit_block(statement.orelse, state.clone())
            handled = True
        elif isinstance(statement, ast.While):
            self._visit_block(statement.body, state.clone())
            self._visit_block(statement.orelse, state.clone())
            handled = True
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            body = state.clone()
            for item in statement.items:
                if item.optional_vars is not None:
                    body.forget(_bound_target_names(item.optional_vars))
            self._visit_block(statement.body, body)
            handled = True
        elif isinstance(statement, (ast.Try, ast.TryStar)):
            self._visit_block(statement.body, state.clone())
            self._visit_block(statement.orelse, state.clone())
            self._visit_block(statement.finalbody, state.clone())
            for handler in statement.handlers:
                self._visit_block(handler.body, state.clone())
            handled = True
        elif isinstance(statement, ast.Match):
            for case in statement.cases:
                self._visit_block(case.body, state.clone())
            handled = True
        else:
            handled = False
        return handled


def _scan_python(path: Path) -> list[BoundaryViolation]:
    violations: list[BoundaryViolation] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as error:
        return [BoundaryViolation(path, 1, f"Cannot parse Python source: {error}")]

    inside_safety = _is_under(path, SAFETY_ROOT)
    approved_response_aliases = _approved_response_aliases(tree)
    importlib_aliases, import_module_aliases = _dynamic_import_aliases(tree)
    violations.extend(_dynamic_loader_surface_violations(path, tree))
    violations.extend(_public_safety_surface_violations(path, tree))
    if not inside_safety:
        violations.extend(
            _external_approved_response_declaration_violations(
                path,
                tree,
                approved_response_aliases,
            )
        )
        violations.extend(
            _ApprovedResponseFlowAnalyzer(path, approved_response_aliases).analyze(tree)
        )
    for node in ast.walk(tree):
        violations.extend(
            _protected_mint_import_violations(
                node,
                path,
                inside_safety,
                importlib_aliases,
                import_module_aliases,
            )
        )
        if isinstance(node, ast.ClassDef):
            if node.name == "ApprovedResponse" and not inside_safety:
                violations.append(
                    BoundaryViolation(
                        path,
                        node.lineno,
                        "ApprovedResponse may be defined only under packages/safety",
                    )
                )
            elif not inside_safety and any(
                _references_approved_response(base, approved_response_aliases)
                for base in node.bases
            ):
                violations.append(
                    BoundaryViolation(
                        path,
                        node.lineno,
                        "ApprovedResponse subclassing is forbidden outside packages/safety",
                    )
                )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "ApprovedResponse" and not inside_safety:
                violations.append(
                    BoundaryViolation(
                        path,
                        node.lineno,
                        "ApprovedResponse may be defined only under packages/safety",
                    )
                )
        elif (
            isinstance(node, ast.Call)
            and _call_name(node) in approved_response_aliases
            and not inside_safety
        ):
            violations.append(
                BoundaryViolation(
                    path,
                    node.lineno,
                    "ApprovedResponse construction is forbidden outside packages/safety",
                )
            )
    return violations


def _walk_objects(value: Any) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    if isinstance(value, dict):
        objects.append(value)
        for child in value.values():
            objects.extend(_walk_objects(child))
    elif isinstance(value, list):
        for child in value:
            objects.extend(_walk_objects(child))
    return objects


def _is_speech_task_name(value: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(value).casefold())
    return "speechtask" in normalized


def _is_speech_task_container_key(value: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(value).casefold())
    return normalized == "speechtask"


def _speech_task_field_tokens(value: str) -> set[str]:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    return {token for token in re.split(r"[^a-z0-9]+", separated.casefold()) if token}


def _is_forbidden_speech_task_field(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", value.casefold())
    tokens = _speech_task_field_tokens(value)
    return normalized in FORBIDDEN_SPEECH_TASK_FIELDS or bool(
        tokens.intersection({"content", "ssml", "text"})
    )


def _resolve_local_schema_ref(document: dict[str, Any], reference: object) -> dict[str, Any] | None:
    if not isinstance(reference, str) or not reference.startswith("#/"):
        return None
    current: object = document
    for raw_token in reference[2:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            return None
        current = current[token]
    return current if isinstance(current, dict) else None


def _find_speech_task_roots(document: Any, path: Path) -> list[dict[str, Any]]:
    if not isinstance(document, dict):
        return []
    roots: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(root: dict[str, Any]) -> None:
        identity = id(root)
        if identity not in seen:
            seen.add(identity)
            roots.append(root)

    if _is_speech_task_name(path.stem) or _is_speech_task_name(document.get("title", "")):
        add(document)

    for schema_object in _walk_objects(document):
        if _is_speech_task_name(schema_object.get("title", "")):
            add(schema_object)
        for key, value in schema_object.items():
            if not _is_speech_task_container_key(key) or not isinstance(value, dict):
                continue
            if set(value) == {"$ref"}:
                add(_resolve_local_schema_ref(document, value["$ref"]) or value)
            else:
                add(value)
    return roots


def _speech_task_violation(path: Path, message: str) -> BoundaryViolation:
    return BoundaryViolation(path, 1, message)


def _validate_speech_task_properties(
    path: Path, properties: dict[str, Any]
) -> list[BoundaryViolation]:
    violations: list[BoundaryViolation] = []
    forbidden = {
        field
        for field in properties
        if isinstance(field, str) and _is_forbidden_speech_task_field(field)
    }
    if forbidden:
        violations.append(
            _speech_task_violation(
                path,
                "SpeechTask schema exposes forbidden raw fields: " + ", ".join(sorted(forbidden)),
            )
        )
    outside_allowlist = {field for field in properties if field not in ALLOWED_SPEECH_TASK_FIELDS}
    if outside_allowlist:
        violations.append(
            _speech_task_violation(
                path,
                "SpeechTask schema fields must use the identifier-only allowlist: "
                + ", ".join(sorted(outside_allowlist)),
            )
        )
    for field, field_schema in properties.items():
        if not isinstance(field_schema, dict):
            violations.append(
                _speech_task_violation(path, f"SpeechTask field schema must be an object: {field}")
            )
            continue
        unsupported_field_keywords = sorted(
            keyword
            for keyword in field_schema
            if keyword not in ALLOWED_SPEECH_TASK_PROPERTY_SCHEMA_KEYWORDS
            and not keyword.startswith("x-")
        )
        if unsupported_field_keywords:
            violations.append(
                _speech_task_violation(
                    path,
                    f"SpeechTask field {field} uses unsupported schema keywords: "
                    + ", ".join(unsupported_field_keywords),
                )
            )
        if field_schema.get("type") not in ALLOWED_SPEECH_TASK_VALUE_TYPES:
            violations.append(
                _speech_task_violation(
                    path,
                    f"SpeechTask field {field} must be a scalar identifier or ordering value",
                )
            )
        if field in UUID_SPEECH_TASK_FIELDS and field_schema.get("format") != "uuid":
            violations.append(
                _speech_task_violation(
                    path,
                    f"SpeechTask identifier field {field} must use format uuid",
                )
            )
    return violations


def _validate_speech_task_root(path: Path, speech_task: dict[str, Any]) -> list[BoundaryViolation]:
    violations: list[BoundaryViolation] = []
    properties = speech_task.get("properties")
    required = speech_task.get("required")
    if speech_task.get("type") != "object":
        violations.append(
            _speech_task_violation(path, "SpeechTask schema must explicitly declare type object")
        )
    if not (
        speech_task.get("additionalProperties") is False
        or speech_task.get("unevaluatedProperties") is False
    ):
        violations.append(
            _speech_task_violation(path, "SpeechTask schema must reject undeclared properties")
        )
    if not isinstance(properties, dict) or "approved_response_id" not in properties:
        violations.append(
            _speech_task_violation(path, "SpeechTask schema must define approved_response_id")
        )
    if not isinstance(required, list) or "approved_response_id" not in required:
        violations.append(
            _speech_task_violation(path, "SpeechTask schema must require approved_response_id")
        )
    unsupported_keywords = sorted(
        {
            keyword
            for schema_object in _walk_objects(speech_task)
            for keyword in FORBIDDEN_SPEECH_TASK_SCHEMA_KEYWORDS
            if keyword in schema_object
        }
    )
    if unsupported_keywords:
        violations.append(
            _speech_task_violation(
                path,
                "SpeechTask schema uses unsupported property-shaping keywords: "
                + ", ".join(unsupported_keywords),
            )
        )
    if isinstance(properties, dict):
        violations.extend(_validate_speech_task_properties(path, properties))
    return violations


def _scan_speech_task_schema(path: Path) -> list[BoundaryViolation]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return [_speech_task_violation(path, f"Cannot parse JSON Schema: {error}")]
    return [
        violation
        for speech_task in _find_speech_task_roots(document, path)
        for violation in _validate_speech_task_root(path, speech_task)
    ]


def _scan_speech_task_schemas() -> list[BoundaryViolation]:
    return [
        violation
        for path in sorted((REPOSITORY_ROOT / "specs").rglob("*.schema.json"))
        for violation in _scan_speech_task_schema(path)
    ]


def find_violations() -> list[BoundaryViolation]:
    violations: list[BoundaryViolation] = []
    for path in _python_paths():
        violations.extend(_scan_python(path))
    violations.extend(_scan_speech_task_schemas())
    return sorted(violations, key=lambda violation: (str(violation.path), violation.line))


def _fail(violations: list[BoundaryViolation]) -> NoReturn:
    for violation in violations:
        print(violation.render(), file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    violations = find_violations()
    if violations:
        _fail(violations)
    print("Architecture boundary checks passed")


if __name__ == "__main__":
    main()
