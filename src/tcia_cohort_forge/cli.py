from __future__ import annotations

import json as jmod
import os

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from tcia_cohort_forge.client import NbiaClient
from tcia_cohort_forge.cohort import CohortBuilder
from tcia_cohort_forge.config import Settings
from tcia_cohort_forge.downloader import CohortDownloader
from tcia_cohort_forge.exporter import (
    export_collections_csv,
    export_manifest_csv,
    export_manifest_json,
    export_patients_csv,
    export_series_csv,
    export_studies_csv,
)
from tcia_cohort_forge.models import CohortCriteria, CohortManifest, SeriesInfo

app = typer.Typer(
    name="tcia-cohort-forge",
    help="Query, browse, and download patient cohorts from The Cancer Imaging Archive (TCIA)",
)
console = Console()
err_console = Console(stderr=True)


def _get_client() -> NbiaClient:
    settings = Settings.from_env()
    return NbiaClient(settings)


@app.callback()
def _main() -> None:
    pass


@app.command()
def collections(
    output: str | None = typer.Option(
        None, "--output", "-o", help="Export to CSV file"
    ),
) -> None:
    """List all TCIA collections with patient counts."""
    with _get_client() as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Fetching collections...", total=None)
            cols = client.get_collections()

    if not cols:
        err_console.print("[yellow]No collections found.[/yellow]")
        raise typer.Exit(1)

    table = Table(title=f"TCIA Collections ({len(cols)})")
    table.add_column("Collection", style="cyan")
    table.add_column("Patients", justify="right")
    table.add_column("Access", justify="center")

    for c in cols:
        access = "[green]Public[/green]" if c.authorized else "[red]Restricted[/red]"
        table.add_row(c.collection, str(c.count), access)

    console.print(table)

    if output:
        path = export_collections_csv(cols, output)
        console.print(f"[green]Exported to {path}[/green]")


@app.command()
def patients(
    collection: str = typer.Argument(..., help="Collection name"),
    modality: str | None = typer.Option(
        None, "--modality", "-m", help="Filter by modality"
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Export to CSV file"
    ),
) -> None:
    """List patients in a collection."""
    with _get_client() as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Fetching patients...", total=None)

            if modality:
                pats = client.get_patients_by_modality(collection, modality)
            else:
                pats = client.get_patients(collection)

    if not pats:
        err_console.print(f"[yellow]No patients found in '{collection}'.[/yellow]")
        raise typer.Exit(1)

    table = Table(title=f"Patients in {collection} ({len(pats)})")
    table.add_column("Patient ID", style="cyan")
    table.add_column("Sex")
    table.add_column("Phantom")

    for p in pats[:200]:
        phantom = "[yellow]Yes[/yellow]" if p.phantom else "No"
        table.add_row(p.patient_id, p.patient_sex or "N/A", phantom)
    if len(pats) > 200:
        table.add_row("...", f"(+{len(pats) - 200} more)", "")

    console.print(table)

    if output:
        path = export_patients_csv(pats, output)
        console.print(f"[green]Exported to {path}[/green]")


@app.command()
def studies(
    collection: str = typer.Argument(..., help="Collection name"),
    patient: str | None = typer.Option(
        None, "--patient", "-p", help="Filter by patient ID"
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Export to CSV file"
    ),
) -> None:
    """List studies in a collection."""
    with _get_client() as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Fetching studies...", total=None)
            sts = client.get_studies(collection, patient_id=patient)

    if not sts:
        err_console.print(f"[yellow]No studies found in '{collection}'.[/yellow]")
        raise typer.Exit(1)

    table = Table(title=f"Studies in {collection} ({len(sts)})")
    table.add_column("Study UID (last 16)")
    table.add_column("Date")
    table.add_column("Description")
    table.add_column("Patient")
    table.add_column("Series")

    for s in sts[:100]:
        table.add_row(
            s.study_instance_uid[-16:],
            s.study_date or "N/A",
            s.study_description[:40] if s.study_description else "N/A",
            s.patient_id,
            str(s.series_count),
        )
    if len(sts) > 100:
        table.add_row("...", f"(+{len(sts) - 100} more)", "", "", "")

    console.print(table)

    if output:
        path = export_studies_csv(sts, output)
        console.print(f"[green]Exported to {path}[/green]")


@app.command()
def series(
    collection: str = typer.Argument(..., help="Collection name"),
    patient: str | None = typer.Option(
        None, "--patient", "-p", help="Filter by patient ID"
    ),
    modality: str | None = typer.Option(
        None, "--modality", "-m", help="Filter by modality (CT, MR, etc.)"
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Export to CSV file"
    ),
) -> None:
    """List DICOM series in a collection."""
    with _get_client() as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Fetching series...", total=None)
            ser = client.get_series(collection, patient_id=patient)

    if modality:
        mod_lower = modality.lower()
        ser = [s for s in ser if s.modality.lower() == mod_lower]

    if not ser:
        err_console.print("[yellow]No series found.[/yellow]")
        raise typer.Exit(1)

    table = Table(title=f"Series in {collection} ({len(ser)})")
    table.add_column("Series UID (last 12)")
    table.add_column("Modality")
    table.add_column("Body Part")
    table.add_column("Description")
    table.add_column("Patient")

    for s in ser[:100]:
        table.add_row(
            s.series_instance_uid[-12:],
            s.modality or "N/A",
            s.body_part_examined or "N/A",
            s.series_description[:30] if s.series_description else "N/A",
            s.patient_id,
        )
    if len(ser) > 100:
        table.add_row("...", f"(+{len(ser) - 100} more)", "", "", "")

    console.print(table)

    if output:
        path = export_series_csv(ser, output)
        console.print(f"[green]Exported to {path}[/green]")


@app.command()
def search(
    collection: str = typer.Argument(..., help="Collection name"),
    modality: str | None = typer.Option(
        None, "--modality", "-m", help="Filter by modality"
    ),
    body_part: str | None = typer.Option(
        None, "--body-part", "-b", help="Filter by body part examined"
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Export cohort manifest to CSV"
    ),
    json_output: str | None = typer.Option(
        None, "--json", "-j", help="Export cohort manifest to JSON"
    ),
) -> None:
    """Build a cohort by searching TCIA with criteria."""
    criteria = CohortCriteria(collection=collection)
    if modality:
        criteria.modalities = [m.strip() for m in modality.split(",")]
    if body_part:
        criteria.body_parts = [b.strip() for b in body_part.split(",")]
    with _get_client() as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Building cohort...", total=None)
            manifest = CohortBuilder(client).build(criteria)

    if manifest.total_series == 0:
        err_console.print(
            "[yellow]No matching series found for the given criteria.[/yellow]"
        )
        raise typer.Exit(1)

    console.print(
        f"[green]Cohort built:[/green] {manifest.total_patients} patients, "
        f"{manifest.total_studies} studies, {manifest.total_series} series"
    )

    table = Table(title="Matched Series (first 50)")
    table.add_column("Patient")
    table.add_column("Modality")
    table.add_column("Body Part")
    table.add_column("Series UID (last 12)")

    for s in manifest.series[:50]:
        table.add_row(
            s.patient_id,
            s.modality,
            s.body_part_examined,
            s.series_instance_uid[-12:],
        )
    console.print(table)

    if output:
        path = export_manifest_csv(manifest, output)
        console.print(f"[green]CSV manifest exported to {path}[/green]")
    if json_output:
        path = export_manifest_json(manifest, json_output)
        console.print(f"[green]JSON manifest exported to {path}[/green]")


@app.command()
def download(
    series_uid: str = typer.Argument(..., help="SeriesInstanceUID to download"),
    output_dir: str = typer.Option(
        "downloads", "--output-dir", "-o", help="Output directory"
    ),
) -> None:
    """Download a single DICOM series."""
    info = SeriesInfo(series_instance_uid=series_uid)
    with _get_client() as client:
        downloader = CohortDownloader(client)
        try:
            size = client.get_series_size(series_uid)
            info.num_images = size.image_count
            info.series_size = size.series_size
        except Exception:
            pass

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Downloading series...", total=None)
            result = downloader.download_series(info, output_dir=output_dir)

    if result.errors:
        for err in result.errors:
            err_console.print(f"[red]{err}[/red]")

    console.print(
        f"[green]Downloaded {result.total_files} files ({result.total_series} series)"
        f" to {os.path.abspath(output_dir)}[/green]"
    )


@app.command()
def download_cohort(
    manifest_file: str = typer.Argument(
        ..., help="Path to JSON manifest file from search --json"
    ),
    output_dir: str = typer.Option(
        "downloads", "--output-dir", "-o", help="Output directory"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be downloaded"
    ),
) -> None:
    """Download all series in a cohort manifest."""
    with open(manifest_file, encoding="utf-8") as f:
        data = jmod.load(f)

    series_list = [SeriesInfo(**s) for s in data.get("series", [])]
    manifest = CohortCriteria(collection="")
    cm = CohortManifest(criteria=manifest, series=series_list)
    cm.total_series = len(series_list)

    with _get_client() as client:
        downloader = CohortDownloader(client)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                description="Downloading cohort...", total=cm.total_series
            )
            result = downloader.download_manifest(
                cm, output_dir=output_dir, dry_run=dry_run
            )

    if result.errors:
        for err in result.errors:
            err_console.print(f"[red]{err}[/red]")

    if dry_run:
        console.print(
            f"[yellow]Dry-run: {result.total_series} series would be downloaded[/yellow]"
        )
    else:
        console.print(
            f"[green]Downloaded {result.total_files} files from {result.total_series} series"
            f" to {os.path.abspath(output_dir)}[/green]"
        )


@app.command()
def info(
    collection: str = typer.Argument(..., help="Collection name"),
) -> None:
    """Show summary info about a collection."""
    with _get_client() as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Fetching collection info...", total=None)
            summary = CohortBuilder(client).get_collection_summary(collection)

    console.print(f"[bold]Collection:[/bold] {collection}")
    console.print(f"[bold]Patients:[/bold] {summary['patients']}")
    console.print(f"[bold]Studies:[/bold] {summary['studies']}")
    console.print(f"[bold]Series:[/bold] {summary['series']}")
    modalities_list: list[str] = summary["modality_list"]
    body_parts_list: list[str] = summary["body_part_list"]
    console.print(f"[bold]Modalities:[/bold] {', '.join(modalities_list)}")
    console.print(f"[bold]Body Parts:[/bold] {', '.join(body_parts_list)}")


if __name__ == "__main__":
    app()
