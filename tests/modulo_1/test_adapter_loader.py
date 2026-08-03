"""Tests para el cargador de adaptadores YAML."""

from __future__ import annotations

from pathlib import Path

import pytest

from modulo_1_servicio.scraping.adapters.loader import AdapterLoader


class TestAdapterLoader:
    def test_load_from_nonexistent_dir(self) -> None:
        """Directorio inexistente retorna lista vacía."""
        loader = AdapterLoader(adapters_dir="/nonexistent/path")
        result = loader.load_all()
        assert result == []

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        """Carga correctamente un archivo YAML válido."""
        yaml_file = tmp_path / "test_site.yaml"
        yaml_file.write_text(
            "name: test_site\n"
            "site: example.com\n"
            "vertical: test\n"
            "search_url: https://example.com/search?q={query}\n"
            "container_selector: div.result\n"
            "fields:\n"
            "  - name: title\n"
            "    selector: h2.title\n"
            "    type: text\n",
            encoding="utf-8",
        )

        loader = AdapterLoader(adapters_dir=tmp_path)
        adapters = loader.load_all()

        assert len(adapters) == 1
        adapter = adapters[0]
        assert adapter.name == "test_site"
        assert adapter.site == "example.com"
        assert adapter.vertical == "test"
        assert len(adapter.fields) == 1
        assert adapter.fields[0].name == "title"

    def test_load_field_required_default_true(self, tmp_path: Path) -> None:
        """required por defecto es True si no se especifica."""
        (tmp_path / "site.yaml").write_text(
            "name: site\nsite: x.com\nvertical: test\n"
            "search_url: https://x.com\n"
            "fields:\n  - name: t\n    selector: h1\n",
            encoding="utf-8",
        )
        loader = AdapterLoader(adapters_dir=tmp_path)
        adapters = loader.load_all()
        assert adapters[0].fields[0].required is True

    def test_load_field_required_false_override(self, tmp_path: Path) -> None:
        """required=False se respeta del YAML (patrón Timbirichi precio)."""
        (tmp_path / "site.yaml").write_text(
            "name: site\nsite: x.com\nvertical: test\n"
            "search_url: https://x.com\n"
            "fields:\n"
            "  - name: precio\n    selector: precio\n    type: price\n"
            "    required: false\n",
            encoding="utf-8",
        )
        loader = AdapterLoader(adapters_dir=tmp_path)
        adapters = loader.load_all()
        assert adapters[0].fields[0].required is False

    def test_load_real_timbirichi_adapter(self) -> None:
        """El adaptador real de Timbirichi carga y usa selector 'self'."""
        loader = AdapterLoader(adapters_dir=Path("adapters"))
        adapters = loader.load_all()
        timbirichi = next((a for a in adapters if a.name == "timbirichi"), None)
        assert timbirichi is not None
        assert timbirichi.container_selector == "a.anuncio-list"
        assert "self" in [f.selector for f in timbirichi.fields]
        assert "location" in (timbirichi.canonical_map or {})

    def test_get_all_after_load(self, tmp_path: Path) -> None:
        """get_all retorna todos los adaptadores cargados."""
        (tmp_path / "a.yaml").write_text(
            "name: site_a\nsite: a.com\nvertical: test\n"
            "search_url: https://a.com\nfields:\n  - name: t\n    selector: h1\n",
        )
        (tmp_path / "b.yaml").write_text(
            "name: site_b\nsite: b.com\nvertical: other\n"
            "search_url: https://b.com\nfields:\n  - name: t\n    selector: h1\n",
        )

        loader = AdapterLoader(adapters_dir=tmp_path)
        loader.load_all()

        assert loader.count == 2
        assert len(loader.get_all()) == 2

    def test_get_by_vertical(self, tmp_path: Path) -> None:
        """Filtra correctamente por vertical."""
        (tmp_path / "cars.yaml").write_text(
            "name: auto_mercadolibre\nsite: mercadolibre.com.mx\nvertical: cars\n"
            "search_url: https://mercadolibre.com.mx/search?q={query}\n"
            "fields:\n  - name: precio\n    selector: .price\n",
        )
        (tmp_path / "jobs.yaml").write_text(
            "name: jobs_occ\nsite: occ.com.mx\nvertical: jobs\n"
            "search_url: https://occ.com.mx/search?q={query}\n"
            "fields:\n  - name: salario\n    selector: .salary\n",
        )

        loader = AdapterLoader(adapters_dir=tmp_path)
        loader.load_all()

        cars = loader.get_by_vertical("cars")
        assert len(cars) == 1
        assert cars[0].name == "auto_mercadolibre"

        jobs = loader.get_by_vertical("jobs")
        assert len(jobs) == 1
        assert jobs[0].name == "jobs_occ"

        empty = loader.get_by_vertical("real_estate")
        assert empty == []

    def test_get_by_name(self, tmp_path: Path) -> None:
        """Obtiene un adaptador por su nombre."""
        (tmp_path / "site.yaml").write_text(
            "name: mi_sitio\nsite: example.com\nvertical: test\n"
            "search_url: https://example.com\n"
            "fields:\n  - name: t\n    selector: h1\n",
        )

        loader = AdapterLoader(adapters_dir=tmp_path)
        loader.load_all()

        adapter = loader.get("mi_sitio")
        assert adapter is not None
        assert adapter.name == "mi_sitio"

        assert loader.get("no_existe") is None

    def test_skip_invalid_yaml(self, tmp_path: Path) -> None:
        """Archivo YAML inválido se omite sin crash."""
        (tmp_path / "invalid.yaml").write_text(
            "name: incomplete\n",  # Faltan campos requeridos
            encoding="utf-8",
        )

        loader = AdapterLoader(adapters_dir=tmp_path)
        adapters = loader.load_all()

        # Debe omitir el inválido y retornar vacío
        assert adapters == []

    def test_skip_non_dict_yaml(self, tmp_path: Path) -> None:
        """Archivo YAML que no es un dict se omite."""
        (tmp_path / "list.yaml").write_text(
            "- item1\n- item2\n",
            encoding="utf-8",
        )

        loader = AdapterLoader(adapters_dir=tmp_path)
        adapters = loader.load_all()

        assert adapters == []

    def test_load_only_yaml_files(self, tmp_path: Path) -> None:
        """Solo archivos .yaml/.yml se cargan, otros no."""
        (tmp_path / "valid.yaml").write_text(
            "name: ok\nsite: ok.com\nvertical: test\n"
            "search_url: https://ok.com\nfields:\n  - name: t\n    selector: h1\n",
        )
        (tmp_path / "not.txt").write_text("esto no es yaml")
        (tmp_path / "also.json").write_text('{"name": "nope"}')

        loader = AdapterLoader(adapters_dir=tmp_path)
        adapters = loader.load_all()

        assert len(adapters) == 1
        assert adapters[0].name == "ok"

    def test_count_property(self, tmp_path: Path) -> None:
        """Propiedad count refleja cantidad de adaptadores."""
        (tmp_path / "a.yaml").write_text(
            "name: a\nsite: a.com\nvertical: test\n"
            "search_url: https://a.com\nfields:\n  - name: t\n    selector: h1\n",
        )

        loader = AdapterLoader(adapters_dir=tmp_path)
        assert loader.count == 0  # Antes de load_all
        loader.load_all()
        assert loader.count == 1
