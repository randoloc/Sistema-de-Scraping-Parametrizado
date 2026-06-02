"""Tests para el cargador de configuración YAML/JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scrapper_generico.config.schema import load_config, load_config_from_dict
from scrapper_generico.core.models import (
    FieldType,
    OutputFormat,
    ScrapeConfig,
    SourceType,
)


class TestLoadConfigFromDict:
    def test_minimal_config(self, sample_config_dict: dict) -> None:
        config = load_config_from_dict(sample_config_dict)
        assert isinstance(config, ScrapeConfig)
        assert config.source_type == SourceType.WEB_PAGE
        assert config.source == "https://example.com/products"
        assert len(config.fields) == 3
        assert config.output_format == OutputFormat.JSON

    def test_field_types(self, sample_config_dict: dict) -> None:
        config = load_config_from_dict(sample_config_dict)
        assert config.fields[0].field_type == FieldType.TEXT
        assert config.fields[1].field_type == FieldType.PRICE
        assert config.fields[2].field_type == FieldType.URL

    def test_filters_parsed(self, sample_config_dict: dict) -> None:
        config = load_config_from_dict(sample_config_dict)
        assert config.filters.max_results == 10
        assert config.filters.deduplicate is True

    def test_missing_source_raises(self) -> None:
        with pytest.raises(KeyError):
            load_config_from_dict({"source_type": "web_page", "fields": []})

    def test_invalid_source_type_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid_source"):
            load_config_from_dict(
                {
                    "source_type": "invalid_source",
                    "source": "https://example.com",
                    "fields": [],
                }
            )


class TestLoadConfigFromFile:
    @pytest.fixture
    def yaml_file(self, tmp_path: Path, sample_config_dict: dict) -> Path:
        path = tmp_path / "config.yaml"
        with open(path, "w") as f:
            yaml.dump(sample_config_dict, f)
        return path

    @pytest.fixture
    def json_file(self, tmp_path: Path, sample_config_dict: dict) -> Path:
        path = tmp_path / "config.json"
        with open(path, "w") as f:
            json.dump(sample_config_dict, f)
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
