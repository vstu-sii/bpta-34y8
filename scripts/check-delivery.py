"""Check Lab 2 artifacts, API compatibility and compose/C4 boundaries offline."""

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def main():
    required = [
        "aact.config.ts",
        "docs/architecture/c4-context.puml",
        "docs/architecture/c4-container.puml",
        "docs/architecture/c4-context.svg",
        "docs/architecture/c4-container.svg",
        "docs/adr/ADR-001-single-data-owner.md",
        "docs/adr/ADR-002-ai-boundary.md",
        "frontend/prototype/index.html",
        "frontend/prototype/app.js",
        "frontend/prototype/style.css",
        "database/schema.sql",
        "database/erd.puml",
        "database/erd.svg",
        "database/migrations/README.md",
        "compose.dev.yml",
        "package-lock.json",
    ]
    for name in required:
        assert (ROOT / name).is_file(), name
    for name in ("upload", "approval", "review", "mobile"):
        data = (ROOT / f"frontend/prototype/screenshots/{name}.png").read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n"), name
    for path in (ROOT / "docs/adr").glob("*.md"):
        assert "## Цена решения" in path.read_text("utf-8"), path
    api_path = ROOT / "api/openapi.yaml"
    assert api_path.read_bytes() == (ROOT / "docs/api/openapi.yaml").read_bytes()
    api = yaml.safe_load(api_path.read_text("utf-8"))
    assert api["openapi"] == "3.1.0"
    schemas = api["components"]["schemas"]
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    request = {
        "$ref": "#/components/schemas/CreateGenerationJobRequest",
        "components": api["components"],
    }
    Draft202012Validator(request).validate(
        {
            "document_id": "00000000-0000-4000-8000-000000000001",
            "prompt_version": "cards-v2",
            "exam_questions": ["Что такое стек?"],
            "chunks": [
                {
                    "chunk_id": 1,
                    "source_locator": "block-1",
                    "text": "Стек использует LIFO.",
                }
            ],
        }
    )
    compose = yaml.safe_load((ROOT / "compose.dev.yml").read_text("utf-8"))
    services = compose["services"]
    assert set(services) == {"app", "web", "agent", "db"}
    assert all("healthcheck" in item for item in services.values())
    assert "ports" not in services["db"] and "ports" not in services["agent"]
    assert set(services["db"]["networks"]) & set(services["agent"]["networks"]) == set()
    alias = api["servers"][0]["url"]
    assert (
        alias
        == services["app"]["environment"]["AI_SERVICE_URL"]
        == "http://ai-service:8000"
    )
    assert "ai-service" in services["agent"]["networks"]["ai"]["aliases"]
    assert services["agent"]["environment"]["PORT"] == "8000"
    sql = (ROOT / "database/schema.sql").read_text("utf-8")
    for label in schemas["CardType"]["enum"]:
        assert f"'{label}'" in sql, label
    for label in schemas["AnswerEvaluation"]["properties"]["status"]["enum"]:
        assert f"'{label}'" in sql, label
    print(
        json.dumps(
            {
                "status": "PASS",
                "artifacts": len(required),
                "screenshots": 4,
                "api_schemas": len(schemas),
                "api_compose_address": alias,
                "agent_db_shared_networks": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
