"""Tests para el cargador de configuración."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from modulo_1_servicio.config.schema import load_config, load_config_from_dict
from modulo_1_servicio.scraping.models import FieldType, OutputFormat, SourceType


@pytest.fixture
def sample_config() -> dict[str, Any]:
    return {
        "source_type": "web_page",
        "source": "https://example.com/products",
        "container_selector": ".product",
        "fields": [
            {"name": "title", "selector": ".title", "type": "text"},
            {"name": "price", "selector": ".price", "type": "price"},
        ],
        "filters": {"max_results": 10, "deduplicate": True},
        "delivery": {
            "emails": ["user@example.com"],
            "whatsapp_numbers": ["521234567890"],
        },
    }


class TestLoadConfigFromDict:
    def test_minimal(self, sample_config: dict[str, Any]) -> None:
        config = load_config_from_dict(sample_config)
        assert config.source_type == SourceType.WEB_PAGE
        assert config.source == "https://example.com/products"
        assert len(config.fields) == 2

    def test_field_types(self, sample_config: dict[str, Any]) -> None:
        config = load_config_from_dict(sample_config)
        assert config.fields[0].field_type == FieldType.TEXT
        assert config.fields[1].field_type == FieldType.PRICE

    def test_delivery(self, sample_config: dict[str, Any]) -> None:
        config = load_config_from_dict(sample_config)
        assert "user@example.com" in config.delivery.emails

    def test_missing_source_raises(self) -> None:
        with pytest.raises(KeyError):
            load_config_from_dict({"source_type": "web_page", "fields": []})

    def test_invalid_source_type(self) -> None:
        with pytest.raises(ValueError):
            load_config_from_dict(
                {"source_type": "invalid", "source": "https://x.com", "fields": []}
            )


class TestLoadConfigFromFile:
    @pytest.fixture
    def yaml_file(self, tmp_path: Path, sample_config: dict[str, Any]) -> Path:
        path = tmp_path / "config.yaml"
        with open(path, "w") as f:
            yaml.dump(sample_config, f)
        return path

    @pytest.fixture
    def json_file(self, tmp_path: Path, sample_config: dict[str, Any]) -> Path:
        path = tmp_path / "config.json"
        with open(path, "w") as f:
            json.dump(sample_config, f)
        return path

    def test_load_yaml(self, yaml_file: Path) -> None:
        config = load_config(yaml_file)
        assert config.source == "https://example.com/products"

    def test_load_json(self, json_file: Path) -> None:
        config = load_config(json_file)
        assert config.source == "https://example.com/products"

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")
