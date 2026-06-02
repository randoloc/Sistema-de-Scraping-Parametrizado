"""Interfaz de línea de comandos para ScrapperGenérico."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from scrapper_generico.config.schema import load_config


@click.group()
def main() -> None:
    """ScrapperGenérico — Motor de scraping configurable."""


@main.command()
@click.argument("config_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False),
    help="Ruta de salida (sobrescribe la del archivo de config)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Solo muestra la configuración sin ejecutar el scraping",
)
def run(config_file: str, output: str | None, dry_run: bool) -> None:
    """Ejecuta una operación de scraping desde un archivo de configuración.

    CONFIG_FILE: Ruta al archivo YAML/JSON con la configuración de scraping.
    """
    try:
        config = load_config(config_file)
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Error cargando configuración: {e}", err=True)
        raise click.Abort() from e

    if dry_run:
        click.echo("=== DRY RUN ===")
        click.echo(f"Fuente: {config.source}")
        click.echo(f"Tipo: {config.source_type.value}")
        click.echo(f"Campos a extraer: {len(config.fields)}")
        click.echo(f"Formato salida: {config.output_format.value}")
        return

    # TODO: implementar ejecución real
    click.echo(f"Scraping de {config.source} iniciado...")
    click.echo("(implementación pendiente)")
