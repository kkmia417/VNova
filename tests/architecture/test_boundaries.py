import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tooling.architecture import check_boundaries as architecture_boundaries
from tooling.architecture.check_boundaries import (
    _scan_python,
    _scan_speech_task_schema,
    find_violations,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TYPESCRIPT_BOUNDARY_CHECKER = (
    REPOSITORY_ROOT / "tooling" / "architecture" / "check_typescript_boundaries.mjs"
)
NODE_EXECUTABLE = shutil.which("node")
BRANDED_APPROVED_RESPONSE = (
    "declare const approvedResponseBrand: unique symbol;\n"
    "export interface ApprovedResponse {\n"
    "  readonly id: string;\n"
    "  readonly [approvedResponseBrand]: true;\n"
    "}\n"
)


def _run_typescript_boundary_checker(
    safety_root: Path, safety_model: Path, consumer: Path
) -> subprocess.CompletedProcess[str]:
    if NODE_EXECUTABLE is None:
        raise RuntimeError("Node.js is required for TypeScript architecture boundary tests")
    (safety_root.parents[1] / "package.json").write_text(
        json.dumps({"private": True, "type": "module"}),
        encoding="utf-8",
    )
    return subprocess.run(  # noqa: S603 - executable and every argument are controlled test inputs.
        [
            NODE_EXECUTABLE,
            str(TYPESCRIPT_BOUNDARY_CHECKER),
            "--safety-root",
            str(safety_root),
            str(safety_model),
            str(consumer),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_architecture_boundaries_have_no_violations() -> None:
    assert find_violations() == []


def test_typescript_boundary_checker_is_mandatory_in_root_lint() -> None:
    package = json.loads((REPOSITORY_ROOT / "package.json").read_text(encoding="utf-8"))

    assert TYPESCRIPT_BOUNDARY_CHECKER.is_file()
    assert "node tooling/architecture/check_typescript_boundaries.mjs" in package["scripts"]["lint"]


def test_approved_response_alias_construction_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(
        "from some_package import ApprovedResponse as Response\nAlias = Response\nAlias()\n",
        encoding="utf-8",
    )

    violations = _scan_python(source)

    assert any("construction is forbidden" in violation.message for violation in violations)


def test_approved_response_subclass_construction_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(
        "from some_package import ApprovedResponse as Base\n"
        "Alias = Base\n"
        "class Derived(Alias):\n"
        "    pass\n"
        "Derived()\n",
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_python(source)]

    assert "ApprovedResponse subclassing is forbidden outside packages/safety" in messages
    assert "ApprovedResponse construction is forbidden outside packages/safety" in messages


@pytest.mark.parametrize(
    ("suffix", "source_text", "expected_message"),
    [
        (
            ".py",
            "from vnova_safety import ApprovedResponse as Response\n"
            "def forge() -> list[Response]:\n"
            "    return []\n",
            "ApprovedResponse producer functions are forbidden outside packages/safety",
        ),
        (
            ".py",
            "from vnova_safety import ApprovedResponse as Response\n"
            'async def forge() -> "Response":\n'
            "    raise RuntimeError\n",
            "ApprovedResponse producer functions are forbidden outside packages/safety",
        ),
        (
            ".pyi",
            "from vnova_safety import ApprovedResponse as Response\ndef forge() -> Response: ...\n",
            "Ambient ApprovedResponse producers are forbidden outside packages/safety",
        ),
    ],
)
def test_python_approved_response_producer_annotations_are_rejected(
    tmp_path: Path,
    suffix: str,
    source_text: str,
    expected_message: str,
) -> None:
    source = tmp_path / f"consumer{suffix}"
    source.write_text(source_text, encoding="utf-8")

    messages = [violation.message for violation in _scan_python(source)]

    assert expected_message in messages


@pytest.mark.parametrize(
    ("source_text", "expected_message"),
    [
        (
            "from typing import Any\n"
            "from vnova_safety import ApprovedResponse\n"
            "parsed: Any = object()\n"
            "forged: ApprovedResponse = parsed\n",
            "Untrusted value cannot flow into ApprovedResponse",
        ),
        (
            "from typing import Any\n"
            "from vnova_safety import ApprovedResponse\n"
            "parsed: Any = []\n"
            "forged: list[ApprovedResponse] = parsed\n",
            "Untrusted value cannot flow into an ApprovedResponse container",
        ),
        (
            "from typing import Any, cast as coerce\n"
            "from vnova_safety import ApprovedResponse as Response\n"
            "parsed: Any = object()\n"
            "forged = coerce(Response, parsed)\n",
            "ApprovedResponse casts are forbidden outside packages/safety",
        ),
        (
            "import typing as types\n"
            "from vnova_safety import ApprovedResponse as Response\n"
            "convert = types.cast\n"
            "parsed: object = object()\n"
            "forged = convert(list[Response], parsed)\n",
            "ApprovedResponse casts are forbidden outside packages/safety",
        ),
        (
            "from vnova_safety import ApprovedResponse\nforged: list[ApprovedResponse]\n",
            "Ambient ApprovedResponse values are forbidden outside packages/safety",
        ),
    ],
)
def test_python_untrusted_approved_response_flows_are_rejected(
    tmp_path: Path,
    source_text: str,
    expected_message: str,
) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(source_text, encoding="utf-8")

    messages = [violation.message for violation in _scan_python(source)]

    assert expected_message in messages


@pytest.mark.parametrize(
    "source_text",
    [
        (
            "from typing import cast\n"
            "from vnova_safety import ApprovedResponse as Response\n"
            "def consume(value: Response, values: list[Response]) -> tuple[str, int]:\n"
            "    alias = value\n"
            "    approved: Response = alias\n"
            "    stored: list[Response] = [approved]\n"
            "    forwarded: list[Response] = values\n"
            "    absent: Response | None = None\n"
            '    text = cast(str, "ok")\n'
            "    return text, len(stored) + len(forwarded)\n"
        ),
        (
            "import vnova_safety as safety\n"
            "from vnova_safety import ApprovedResponse as Response\n"
            "def consume() -> str:\n"
            "    factory = safety.approve\n"
            "    approved: Response = factory()\n"
            "    return approved.id\n"
        ),
        (
            "from typing import Annotated, Literal\n"
            'def describe() -> Annotated[str, "ApprovedResponse metadata"]:\n'
            '    return "ok"\n'
            'choice: Literal["ApprovedResponse"] = "ApprovedResponse"\n'
        ),
    ],
)
def test_python_trusted_approved_response_pass_through_is_allowed(
    tmp_path: Path,
    source_text: str,
) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(source_text, encoding="utf-8")

    assert _scan_python(source) == []


def test_python_private_safety_source_keeps_minting_allowances(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    private_mint = internal_root / "mint.py"
    private_mint.write_text(
        "from typing import Any, cast\n"
        "class ApprovedResponse:\n"
        "    pass\n"
        "def mint(value: Any) -> ApprovedResponse:\n"
        "    return cast(ApprovedResponse, value)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(architecture_boundaries, "SAFETY_ROOT", safety_root.resolve())

    assert architecture_boundaries._scan_python(private_mint) == []


def test_generated_python_and_stub_sources_cannot_bypass_approved_response_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated_root = tmp_path / "generated"
    generated_root.mkdir()
    generated_definition = generated_root / "forged.py"
    generated_producer = generated_root / "producer.pyi"
    generated_definition.write_text("class ApprovedResponse: pass\n", encoding="utf-8")
    generated_producer.write_text(
        "from vnova_safety import ApprovedResponse\ndef forge() -> ApprovedResponse: ...\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(architecture_boundaries, "SCAN_ROOTS", (tmp_path,))

    discovered = architecture_boundaries._python_paths()
    definition_messages = [
        violation.message
        for violation in architecture_boundaries._scan_python(generated_definition)
    ]
    producer_messages = [
        violation.message for violation in architecture_boundaries._scan_python(generated_producer)
    ]

    assert generated_definition in discovered
    assert generated_producer in discovered
    assert "ApprovedResponse may be defined only under packages/safety" in definition_messages
    assert (
        "Ambient ApprovedResponse producers are forbidden outside packages/safety"
        in producer_messages
    )


def test_typescript_approved_response_object_construction_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        'export const forged: ApprovedResponse = { id: "forged" };\n',
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse object construction is forbidden" in completed.stderr


def test_typescript_approved_response_read_only_consumption_is_allowed(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "export function approvedId(approved: ApprovedResponse): string {\n"
        "  return approved.id;\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 0, completed.stderr


def test_typescript_approved_response_inheritance_and_assertion_are_rejected(
    tmp_path: Path,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "class Derived implements ApprovedResponse { readonly id = 'forged'; }\n"
        "export const derived = new Derived();\n"
        "export const asserted = { id: 'forged' } as ApprovedResponse;\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse inheritance is forbidden" in completed.stderr
    assert "ApprovedResponse construction is forbidden" in completed.stderr
    assert "ApprovedResponse type assertion is forbidden" in completed.stderr


def test_typescript_approved_response_requires_private_nominal_brand(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    safety_root.mkdir(parents=True)
    safety_model = safety_root / "model.ts"
    safety_model.write_text(
        "export interface ApprovedResponse { readonly id: string }\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, safety_model)

    assert completed.returncode == 1
    assert "readonly private unique-symbol brand" in completed.stderr


def test_typescript_approved_response_brand_must_not_be_exported(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    safety_root.mkdir(parents=True)
    safety_model = safety_root / "model.ts"
    safety_model.write_text(
        "export declare const approvedResponseBrand: unique symbol;\n"
        "export interface ApprovedResponse {\n"
        "  readonly id: string;\n"
        "  readonly [approvedResponseBrand]: true;\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, safety_model)

    assert completed.returncode == 1
    assert "readonly private unique-symbol brand" in completed.stderr


def test_typescript_intermediate_structural_value_cannot_enter_approved_response(
    tmp_path: Path,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "function consume(value: ApprovedResponse): string { return value.id; }\n"
        "const forged = { id: 'forged' };\n"
        "export const result = consume(forged);\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "Untrusted value cannot flow into ApprovedResponse" in completed.stderr


def test_typescript_any_value_cannot_be_assigned_to_approved_response(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "declare const raw: string;\n"
        "const parsed = JSON.parse(raw);\n"
        "export const forged: ApprovedResponse = parsed;\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "Untrusted value cannot flow into ApprovedResponse" in completed.stderr


def test_typescript_any_container_cannot_be_destructured_as_approved_response(
    tmp_path: Path,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "declare const raw: string;\n"
        "const { value }: { value: ApprovedResponse } = JSON.parse(raw);\n"
        "export const approvedId = value.id;\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "Untrusted value cannot flow into an ApprovedResponse container" in completed.stderr


def test_typescript_approved_response_pass_through_is_allowed(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "export function approvedId(value: ApprovedResponse): string {\n"
        "  const alias: ApprovedResponse = value;\n"
        "  return alias.id;\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 0, completed.stderr


def test_typescript_local_readonly_approved_response_storage_is_allowed(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "export function firstId(value: ApprovedResponse): string {\n"
        "  const stored: readonly ApprovedResponse[] = [value];\n"
        "  return stored[0]?.id ?? '';\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 0, completed.stderr


def test_typescript_safety_owned_async_producer_is_allowed(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(
        BRANDED_APPROVED_RESPONSE
        + "export declare function loadApproved(): Promise<ApprovedResponse>;\n",
        encoding="utf-8",
    )
    consumer.write_text(
        'import { loadApproved } from "../packages/safety/model.js";\n'
        "export async function approvedId(): Promise<string> {\n"
        "  const approved = await loadApproved();\n"
        "  return approved.id;\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 0, completed.stderr


def test_typescript_async_approved_response_producer_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "export async function forward(\n"
        "  value: ApprovedResponse,\n"
        "): Promise<ApprovedResponse> {\n"
        "  return value;\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse producer functions are forbidden" in completed.stderr


def test_typescript_approved_response_type_predicate_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "export function forge(value: unknown): value is ApprovedResponse {\n"
        "  return true;\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse type predicates are forbidden" in completed.stderr


def test_typescript_approved_response_clone_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "function clone<T>(value: T): T { return value; }\n"
        "export function forge(value: ApprovedResponse): ApprovedResponse {\n"
        "  return clone(value);\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse-producing calls are forbidden" in completed.stderr


def test_typescript_approved_response_spread_clone_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "function consume(value: ApprovedResponse): string { return value.id; }\n"
        "export function forge(value: ApprovedResponse): string {\n"
        "  const clone = { ...value, id: 'forged' };\n"
        "  return consume(clone);\n"
        "}\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse object construction is forbidden" in completed.stderr


def test_typescript_never_assertion_cannot_enter_approved_response(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "declare const raw: string;\n"
        "function consume(value: ApprovedResponse): string { return value.id; }\n"
        "const forged = JSON.parse(raw) as never;\n"
        "export const result = consume(forged);\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "Untrusted value cannot flow into ApprovedResponse" in completed.stderr


def test_typescript_generic_predicate_cannot_mint_approved_response(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "function claims<T>(value: unknown): value is T { return true; }\n"
        "function consume(value: ApprovedResponse): string { return value.id; }\n"
        "declare const parsed: unknown;\n"
        "export const result = claims<ApprovedResponse>(parsed) ? consume(parsed) : '';\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse generic instantiation is forbidden" in completed.stderr


def test_typescript_approved_response_alias_assertion_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "type Alias = ApprovedResponse;\n"
        "function consume(value: ApprovedResponse): string { return value.id; }\n"
        "const forged = {} as unknown as Alias;\n"
        "export const result = consume(forged);\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse type assertion is forbidden" in completed.stderr


def test_typescript_approved_response_alias_ambient_value_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "type Alias = ApprovedResponse;\n"
        "export declare const forged: Alias;\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "Ambient ApprovedResponse values are forbidden" in completed.stderr


def test_typescript_approved_response_alias_predicate_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "type Alias = ApprovedResponse;\n"
        "export function forge(value: unknown): value is Alias { return true; }\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse type predicates are forbidden" in completed.stderr


def test_typescript_approved_response_alias_generic_instantiation_is_rejected(
    tmp_path: Path,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "type Alias = ApprovedResponse;\n"
        "function claims<T>(value: unknown): value is T { return true; }\n"
        "declare const parsed: unknown;\n"
        "export const result = claims<Alias>(parsed);\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse generic instantiation is forbidden" in completed.stderr


def test_typescript_approved_response_container_alias_assertion_is_rejected(
    tmp_path: Path,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "type Box = { readonly value: ApprovedResponse };\n"
        "declare const raw: string;\n"
        "const box = JSON.parse(raw) as Box;\n"
        "export const approvedId = box.value.id;\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "ApprovedResponse type assertion is forbidden" in completed.stderr


def test_typescript_external_approved_response_value_import_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    external = tmp_path / "external.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    external.write_text(
        'import type { ApprovedResponse } from "./packages/safety/model.js";\n'
        "export declare const forged: ApprovedResponse;\n",
        encoding="utf-8",
    )
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        'import { forged } from "../external.js";\n'
        "function consume(value: ApprovedResponse): string { return value.id; }\n"
        "export const result = consume(forged);\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "Untrusted value cannot flow into ApprovedResponse" in completed.stderr


def test_typescript_safety_owned_approved_response_value_import_is_allowed(
    tmp_path: Path,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(
        BRANDED_APPROVED_RESPONSE + "export declare const approved: ApprovedResponse;\n",
        encoding="utf-8",
    )
    consumer.write_text(
        'import { approved, type ApprovedResponse } from "../packages/safety/model.js";\n'
        "function consume(value: ApprovedResponse): string { return value.id; }\n"
        "export const result = consume(approved);\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 0, completed.stderr


def test_typescript_ambient_approved_response_value_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "export declare const forged: ApprovedResponse;\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "Ambient ApprovedResponse values are forbidden" in completed.stderr


def test_typescript_ambient_approved_response_producer_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import type { ApprovedResponse } from "../packages/safety/model.js";\n'
        "export declare function forge(): ApprovedResponse;\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "Ambient ApprovedResponse producers are forbidden" in completed.stderr


@pytest.mark.parametrize(
    "consumer_source",
    [
        'import { mint } from "../packages/safety/internal/mint.js";\n'
        "export const forged = mint();\n",
        'export { mint } from "../packages/safety/internal/mint.js";\n',
        "export async function loadMint(): Promise<unknown> {\n"
        '  return import("../packages/safety/internal/mint.js");\n'
        "}\n",
        'export { mint } from "../packages/safety/Internal/mint.js";\n',
        'export { mint } from "../packages/safety/_MiNt.JS";\n',
        'export { mint } from "../packages/safety/PrIvAtE/mint.js";\n',
    ],
)
def test_typescript_private_safety_mint_import_is_rejected(
    tmp_path: Path, consumer_source: str
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    private_mint = internal_root / "mint.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    private_mint.write_text("export declare function mint(): unknown;\n", encoding="utf-8")
    consumer.write_text(consumer_source, encoding="utf-8")

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "protected safety mint module" in completed.stderr


@pytest.mark.parametrize(
    "public_source",
    [
        'export { mint } from "./internal/mint.js";\n',
        'import { mint } from "./internal/mint.js";\nexport { mint };\n',
        'import { mint } from "./internal/mint.js";\nexport const exposed = mint;\n',
        'import { mint } from "./internal/mint.js";\n'
        "export function leak(): unknown { return mint; }\n",
        'import { mint } from "./internal/mint.js";\n'
        "export const leaked = { take(): unknown { return mint; } };\n",
        'import { mint } from "./internal/mint.js";\n'
        "export class Leaked { take(): unknown { return mint; } }\n",
        'import { mint } from "./internal/mint.js";\n'
        "export function leak(cap = mint): unknown { return cap; }\n",
        'import { mint } from "./internal/mint.js";\n'
        "export function* leak(): Generator<unknown> { yield mint; }\n",
        'import { mint } from "./internal/mint.js";\n'
        "export class Leak { static capability = mint; }\n",
    ],
)
def test_typescript_safety_public_surface_cannot_export_mint_capability(
    tmp_path: Path,
    public_source: str,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    private_mint = internal_root / "mint.ts"
    public_index = safety_root / "index.ts"
    private_mint.write_text("export declare function mint(): unknown;\n", encoding="utf-8")
    public_index.write_text(public_source, encoding="utf-8")

    completed = _run_typescript_boundary_checker(safety_root, private_mint, public_index)

    assert completed.returncode == 1
    assert (
        "mint capability cannot be exported" in completed.stderr
        or "public safety module cannot import or export" in completed.stderr
    )


def test_typescript_private_safety_module_may_use_mint_internally(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    private_mint = internal_root / "mint.ts"
    internal_consumer = internal_root / "consumer.ts"
    private_mint.write_text("export declare function mint(): unknown;\n", encoding="utf-8")
    internal_consumer.write_text(
        'import { mint } from "./mint.js";\nexport function use(): unknown { return mint(); }\n',
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, private_mint, internal_consumer)

    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    ("suffix", "consumer_source"),
    [
        (".mjs", 'import { mint } from "../packages/safety/internal/mint.js";\n'),
        (".mjs", 'export { mint } from "../packages/safety/internal/mint.js";\n'),
        (".js", 'export const mint = import("../packages/safety/internal/mint.js");\n'),
        (".cjs", 'module.exports = require("../packages/safety/internal/mint.js");\n'),
        (".cjs", 'module.exports = module.require("../packages/safety/internal/mint.js");\n'),
        (
            ".cjs",
            'module.exports = require("../packages/safety/internal/mint.js", undefined);\n',
        ),
        (
            ".cjs",
            'const mintPath = "../packages/safety/internal/mint.js";\n'
            "module.exports = require(mintPath);\n",
        ),
        (".mjs", 'export { mint } from "../packages/safety/Internal/mint.js";\n'),
        (".mjs", 'export { mint } from "../packages/safety/_MiNt.JS";\n'),
        (".mjs", 'export { mint } from "../packages/safety/PrIvAtE/mint.js";\n'),
        (".mjs", 'export { mint } from "@VNova/Safety/Internal/mint.js";\n'),
    ],
)
def test_javascript_private_safety_mint_import_is_rejected(
    tmp_path: Path,
    suffix: str,
    consumer_source: str,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / f"consumer{suffix}"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(consumer_source, encoding="utf-8")

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "protected safety mint module" in completed.stderr


@pytest.mark.parametrize(
    "specifier_kind",
    ["file_url", "uppercase_file_url", "absolute_path"],
)
def test_javascript_private_safety_absolute_import_is_rejected(
    tmp_path: Path,
    specifier_kind: str,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    consumer_root.mkdir()
    private_mint = internal_root / "mint.mjs"
    consumer = consumer_root / "consumer.mjs"
    private_mint.write_text("export function mint() { return undefined; }\n", encoding="utf-8")
    if specifier_kind == "absolute_path":
        specifier = private_mint.resolve().as_posix()
    else:
        specifier = private_mint.resolve().as_uri()
        if specifier_kind == "uppercase_file_url":
            specifier = specifier.replace("file:", "FILE:", 1)
    consumer.write_text(
        f"export {{ mint }} from {json.dumps(specifier)};\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, private_mint, consumer)

    assert completed.returncode == 1
    assert "protected safety mint module" in completed.stderr


def test_javascript_public_safety_module_cannot_import_private_mint(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    private_mint = internal_root / "mint.ts"
    public_index = safety_root / "index.mjs"
    private_mint.write_text("export declare function mint(): unknown;\n", encoding="utf-8")
    public_index.write_text('export { mint } from "./internal/mint.js";\n', encoding="utf-8")

    completed = _run_typescript_boundary_checker(safety_root, private_mint, public_index)

    assert completed.returncode == 1
    assert "public JavaScript safety module" in completed.stderr


def test_javascript_private_safety_module_static_import_is_allowed(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    private_mint = internal_root / "mint.mjs"
    internal_consumer = internal_root / "consumer.mjs"
    private_mint.write_text("export function mint() { return undefined; }\n", encoding="utf-8")
    internal_consumer.write_text(
        'import { mint } from "./mint.mjs";\nexport const value = mint();\n',
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(
        safety_root,
        private_mint,
        internal_consumer,
    )

    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    "consumer_source",
    [
        'module.exports = require("./mint.cjs");\n',
        'module.exports = module["require"]("./mint.cjs");\n',
        'const load = require;\nmodule.exports = load("./mint.cjs");\n',
    ],
)
def test_javascript_private_safety_module_dynamic_loader_fails_closed(
    tmp_path: Path,
    consumer_source: str,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    private_mint = internal_root / "mint.cjs"
    internal_consumer = internal_root / "consumer.cjs"
    private_mint.write_text("module.exports = function mint() {};\n", encoding="utf-8")
    internal_consumer.write_text(consumer_source, encoding="utf-8")

    completed = _run_typescript_boundary_checker(
        safety_root,
        private_mint,
        internal_consumer,
    )

    assert completed.returncode == 1
    assert "Dynamic module-loading primitives are forbidden" in completed.stderr


def test_typescript_import_equals_private_safety_mint_is_rejected(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    consumer_root.mkdir()
    private_mint = internal_root / "mint.cts"
    consumer = consumer_root / "consumer.cts"
    private_mint.write_text(
        "declare function mint(): unknown;\nexport = mint;\n",
        encoding="utf-8",
    )
    consumer.write_text(
        'import mint = require("../packages/safety/internal/mint.cjs");\n'
        "export const forged = mint();\n",
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, private_mint, consumer)

    assert completed.returncode == 1
    assert "protected safety mint module" in completed.stderr


@pytest.mark.parametrize(
    ("suffix", "consumer_source"),
    [
        (".cjs", 'const load = require;\nmodule.exports = load("node:path");\n'),
        (".cjs", 'module.exports = module["require"]("node:path");\n'),
        (
            ".mjs",
            "export async function load(name) { return import(name); }\n",
        ),
        (
            ".mjs",
            'import { createRequire as makeRequire } from "node:module";\n'
            "export const load = makeRequire(import.meta.url);\n",
        ),
    ],
)
def test_javascript_dynamic_module_loaders_fail_closed(
    tmp_path: Path,
    suffix: str,
    consumer_source: str,
) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / f"consumer{suffix}"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(consumer_source, encoding="utf-8")

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "Dynamic module-loading primitives are forbidden" in completed.stderr


def test_typescript_unresolved_program_fails_closed(tmp_path: Path) -> None:
    safety_root = tmp_path / "packages" / "safety"
    consumer_root = tmp_path / "apps"
    safety_root.mkdir(parents=True)
    consumer_root.mkdir()
    safety_model = safety_root / "model.ts"
    consumer = consumer_root / "consumer.ts"
    safety_model.write_text(BRANDED_APPROVED_RESPONSE, encoding="utf-8")
    consumer.write_text(
        'import { missing } from "../missing-module.js";\nexport const value = missing;\n',
        encoding="utf-8",
    )

    completed = _run_typescript_boundary_checker(safety_root, safety_model, consumer)

    assert completed.returncode == 1
    assert "TypeScript program must be error-free for boundary analysis" in completed.stderr


def test_private_mint_module_import_from_package_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(
        "from vnova_safety import _mint as mint\nmint.some_factory()\n",
        encoding="utf-8",
    )

    violations = _scan_python(source)

    assert any("protected safety mint module" in violation.message for violation in violations)


@pytest.mark.parametrize(
    "source_text",
    [
        "from VNova_Safety import _MiNt as mint\n",
        "from vnova_safety.Internal import mint\n",
        "import vnova_safety.PrIvAtE.bridge\n",
    ],
)
def test_python_private_safety_import_is_case_insensitive_on_portable_paths(
    tmp_path: Path,
    source_text: str,
) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(source_text, encoding="utf-8")

    violations = _scan_python(source)

    assert any("protected safety mint module" in violation.message for violation in violations)


@pytest.mark.parametrize(
    "source_text",
    [
        'import importlib\nimportlib.import_module("vnova_safety._mint")\n',
        'import importlib\nimportlib.import_module(name="vnova_safety._mint")\n',
        'import importlib as loader\nloader.import_module("vnova_safety._mint")\n',
        'from importlib import import_module as load\nload("vnova_safety._mint")\n',
        'from importlib import import_module\nload = import_module\nload("vnova_safety._mint")\n',
        '__import__("vnova_safety._mint")\n',
        '__import__("vnova_safety", fromlist=("_mint",))\n',
        'from importlib import import_module\nimport_module("._mint", package="vnova_safety")\n',
        'from importlib import import_module\nimport_module("._mint", "vnova_safety")\n',
        '__import__("vnova_safety", None, None, ("_mint",))\n',
        'from importlib import import_module\nimport_module(".internal.bridge", "vnova_safety")\n',
        "from importlib import import_module\n"
        'import_module("..internal.bridge", "vnova_safety.public")\n',
        '__import__("vnova_safety", None, None, ("internal",))\n',
        'from importlib import import_module\nimport_module("VNova_Safety._MiNt")\n',
        'from importlib import import_module\nimport_module(".Internal.bridge", "VNova_Safety")\n',
        '__import__("VNova_Safety", None, None, ("PrIvAtE",))\n',
    ],
)
def test_private_mint_module_dynamic_import_is_rejected(
    tmp_path: Path,
    source_text: str,
) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(source_text, encoding="utf-8")

    violations = _scan_python(source)

    assert any("protected safety mint module" in violation.message for violation in violations)


@pytest.mark.parametrize(
    "source_text",
    [
        'load = __import__\nload("json")\n',
        'import importlib\nloader = importlib\nloader.import_module("json")\n',
        'from importlib import import_module\nname = "json"\nimport_module(name)\n',
        'from builtins import __import__ as load\nload("json")\n',
        'import builtins\ngetattr(builtins, "__import__")("json")\n',
        "from importlib.util import spec_from_file_location\n",
    ],
)
def test_python_dynamic_module_loaders_fail_closed(
    tmp_path: Path,
    source_text: str,
) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(source_text, encoding="utf-8")

    violations = _scan_python(source)

    assert any(
        "Dynamic module-loading primitives are forbidden" in item.message for item in violations
    )


def test_python_safety_public_surface_cannot_import_mint_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    safety_root = tmp_path / "vnova_safety"
    safety_root.mkdir()
    public_index = safety_root / "__init__.py"
    public_index.write_text("from ._mint import mint\n", encoding="utf-8")
    monkeypatch.setattr(architecture_boundaries, "SAFETY_ROOT", safety_root.resolve())

    violations = architecture_boundaries._scan_python(public_index)

    assert any("private safety modules" in violation.message for violation in violations)


@pytest.mark.parametrize(
    "public_source",
    [
        "def leak():\n    from ._mint import mint\n    return mint\n",
        "from ._mint import mint as _mint\nleak = [_mint for _ in range(1)]\n",
        "from ._mint import mint as _mint\nclass Leak:\n    capability = _mint\n",
        "from ._mint import mint as _mint\ndef leak():\n    yield _mint\n",
        "import importlib\n"
        "def leak():\n"
        '    return importlib.import_module("..internal.bridge", "vnova_safety.public")\n',
    ],
)
def test_python_public_safety_nested_private_import_paths_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    public_source: str,
) -> None:
    safety_root = tmp_path / "vnova_safety"
    safety_root.mkdir()
    public_module = safety_root / "facade.py"
    public_module.write_text(public_source, encoding="utf-8")
    monkeypatch.setattr(architecture_boundaries, "SAFETY_ROOT", safety_root.resolve())

    assert architecture_boundaries._scan_python(public_module)


def test_python_external_import_from_internal_safety_module_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(
        "from vnova_safety.internal.bridge import leak\nleak()\n",
        encoding="utf-8",
    )

    violations = _scan_python(source)

    assert any("protected safety mint module" in violation.message for violation in violations)


def test_python_external_nested_from_import_of_mint_name_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "consumer.py"
    source.write_text("from vnova_safety.facades import _mint\n", encoding="utf-8")

    violations = _scan_python(source)

    assert any("protected safety mint module" in violation.message for violation in violations)


def test_python_unrelated_relative_internal_import_is_allowed(tmp_path: Path) -> None:
    source = tmp_path / "consumer.py"
    source.write_text("from .internal import helper\nhelper()\n", encoding="utf-8")

    assert _scan_python(source) == []


def test_python_indirect_internal_mint_reexport_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    safety_root = tmp_path / "vnova_safety"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    bridge = internal_root / "bridge.py"
    facade = safety_root / "facade.py"
    public_index = safety_root / "__init__.py"
    bridge.write_text(
        "from .._mint import mint\ndef leak():\n    return mint\n",
        encoding="utf-8",
    )
    facade.write_text("from .internal.bridge import leak\n", encoding="utf-8")
    public_index.write_text("from .facade import leak\n", encoding="utf-8")
    monkeypatch.setattr(architecture_boundaries, "SAFETY_ROOT", safety_root.resolve())

    violations = [
        *architecture_boundaries._scan_python(bridge),
        *architecture_boundaries._scan_python(facade),
        *architecture_boundaries._scan_python(public_index),
    ]

    assert any("underscore-prefixed local aliases" in violation.message for violation in violations)


def test_python_private_alias_call_cannot_return_through_public_facade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    safety_root = tmp_path / "vnova_safety"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    facade = safety_root / "facade.py"
    facade.write_text(
        "from .internal.bridge import leak as _leak\ndef leak():\n    return _leak()\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(architecture_boundaries, "SAFETY_ROOT", safety_root.resolve())

    violations = architecture_boundaries._scan_python(facade)

    assert any("cannot return a private safety capability" in item.message for item in violations)


def test_python_public_safety_class_cannot_return_private_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    safety_root = tmp_path / "vnova_safety"
    safety_root.mkdir()
    facade = safety_root / "facade.py"
    facade.write_text(
        "from .internal.bridge import leak as _leak\n"
        "class Leaked:\n"
        "    def take(self):\n"
        "        return _leak()\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(architecture_boundaries, "SAFETY_ROOT", safety_root.resolve())

    violations = architecture_boundaries._scan_python(facade)

    assert any("class cannot return" in item.message for item in violations)


def test_python_public_safety_wrapper_cannot_import_private_mint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    safety_root = tmp_path / "vnova_safety"
    safety_root.mkdir()
    public_gateway = safety_root / "gateway.py"
    public_gateway.write_text(
        "from ._mint import mint as _mint_response\ndef approve():\n    return _mint_response()\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(architecture_boundaries, "SAFETY_ROOT", safety_root.resolve())

    violations = architecture_boundaries._scan_python(public_gateway)

    assert any(
        "public safety module cannot import" in item.message.casefold() for item in violations
    )


def test_python_private_safety_module_may_import_mint_internally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    safety_root = tmp_path / "vnova_safety"
    internal_root = safety_root / "internal"
    internal_root.mkdir(parents=True)
    internal_consumer = internal_root / "consumer.py"
    internal_consumer.write_text("from .._mint import mint\nmint()\n", encoding="utf-8")
    monkeypatch.setattr(architecture_boundaries, "SAFETY_ROOT", safety_root.resolve())

    assert architecture_boundaries._scan_python(internal_consumer) == []


def test_speech_task_raw_text_field_is_rejected(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech-task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "SpeechTask",
                "type": "object",
                "additionalProperties": False,
                "properties": {"approved_response_id": {"type": "string"}, "text": {}},
            }
        ),
        encoding="utf-8",
    )

    violations = _scan_speech_task_schema(schema_path)

    assert any("forbidden raw fields: text" in violation.message for violation in violations)


def test_nested_speech_task_raw_text_field_is_rejected(tmp_path: Path) -> None:
    schema_path = tmp_path / "stage-protocol.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "StageProtocol",
                "$defs": {
                    "SpeechTask": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["approved_response_id"],
                        "properties": {
                            "approved_response_id": {"type": "string"},
                            "text": {"type": "string"},
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    violations = _scan_speech_task_schema(schema_path)

    assert any("forbidden raw fields: text" in violation.message for violation in violations)


def test_speech_task_requires_approved_response_id(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech-task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "SpeechTask",
                "type": "object",
                "required": ["task_id"],
                "properties": {"task_id": {"type": "string"}},
            }
        ),
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_speech_task_schema(schema_path)]

    assert "SpeechTask schema must define approved_response_id" in messages
    assert "SpeechTask schema must require approved_response_id" in messages


def test_speech_task_name_and_forbidden_fields_are_normalized(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech_task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["approved_response_id"],
                "properties": {
                    "approved_response_id": {"type": "string"},
                    "rawText": {"type": "string"},
                },
            }
        ),
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_speech_task_schema(schema_path)]

    assert any("forbidden raw fields: rawText" in message for message in messages)


def test_speech_task_must_reject_undeclared_properties(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech-task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "SpeechTask",
                "type": "object",
                "required": ["approved_response_id"],
                "properties": {"approved_response_id": {"type": "string"}},
            }
        ),
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_speech_task_schema(schema_path)]

    assert "SpeechTask schema must reject undeclared properties" in messages


def test_speech_task_local_ref_target_is_scanned(tmp_path: Path) -> None:
    schema_path = tmp_path / "stage-protocol.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"speech_task": {"$ref": "#/$defs/TaskBody"}},
                "$defs": {
                    "TaskBody": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["approved_response_id"],
                        "properties": {
                            "approved_response_id": {"type": "string"},
                            "raw-text": {"type": "string"},
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_speech_task_schema(schema_path)]

    assert any("forbidden raw fields: raw-text" in message for message in messages)


def test_speech_task_must_explicitly_be_an_object(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech-task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "SpeechTask",
                "additionalProperties": False,
                "required": ["approved_response_id"],
                "properties": {"approved_response_id": {"type": "string"}},
            }
        ),
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_speech_task_schema(schema_path)]

    assert "SpeechTask schema must explicitly declare type object" in messages


def test_speech_task_identifier_only_flat_schema_is_accepted(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech-task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "SpeechTask",
                "type": "object",
                "additionalProperties": False,
                "required": ["approved_response_id"],
                "properties": {
                    "approved_response_id": {"type": "string", "format": "uuid"},
                    "speech_task_id": {"type": "string", "format": "uuid"},
                    "session_epoch": {"type": "integer", "minimum": 0},
                },
            }
        ),
        encoding="utf-8",
    )

    assert _scan_speech_task_schema(schema_path) == []


def test_speech_task_pattern_properties_cannot_smuggle_raw_text(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech-task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "SpeechTask",
                "type": "object",
                "additionalProperties": False,
                "required": ["approved_response_id"],
                "properties": {"approved_response_id": {"type": "string"}},
                "patternProperties": {"^text$": {"type": "string"}},
            }
        ),
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_speech_task_schema(schema_path)]

    assert any(
        "unsupported property-shaping keywords: patternProperties" in message
        for message in messages
    )


def test_speech_task_composition_and_alias_fields_fail_closed(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech-task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "SpeechTask",
                "type": "object",
                "unevaluatedProperties": False,
                "required": ["approved_response_id"],
                "properties": {
                    "approved_response_id": {"type": "string"},
                    "utterance": {"type": "string"},
                },
                "allOf": [{"properties": {"content": {"type": "string"}}}],
            }
        ),
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_speech_task_schema(schema_path)]

    assert any("unsupported property-shaping keywords: allOf" in message for message in messages)
    assert any("identifier-only allowlist: utterance" in message for message in messages)


def test_speech_task_allowed_field_must_have_a_scalar_schema(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech-task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "SpeechTask",
                "type": "object",
                "additionalProperties": False,
                "required": ["approved_response_id"],
                "properties": {"approved_response_id": {}},
            }
        ),
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_speech_task_schema(schema_path)]

    assert any("must be a scalar identifier or ordering value" in message for message in messages)


def test_speech_task_identifier_fields_require_uuid_format(tmp_path: Path) -> None:
    schema_path = tmp_path / "speech-task.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "SpeechTask",
                "type": "object",
                "additionalProperties": False,
                "required": ["approved_response_id"],
                "properties": {"approved_response_id": {"type": "string"}},
            }
        ),
        encoding="utf-8",
    )

    messages = [violation.message for violation in _scan_speech_task_schema(schema_path)]

    assert "SpeechTask identifier field approved_response_id must use format uuid" in messages
