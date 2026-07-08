"""Command-line interface for the cloud migration factory.

Exposes four subcommands wired to the library:

- ``assess`` — read an inventory and write disposition recommendations,
- ``plan-waves`` — group assessed servers into dependency-ordered waves,
- ``status`` — create and advance migration tasks, reporting task counts,
- ``report`` — print a human-readable summary of an assessed/planned inventory.
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from migration_factory import __version__
from migration_factory.assessment import Assessor
from migration_factory.config import get_settings
from migration_factory.logging_config import configure_logging
from migration_factory.models import Server, TaskStatus
from migration_factory.orchestrator import MigrationOrchestrator
from migration_factory.wave_planner import WavePlanner


def _load_inventory(path: Path) -> list[Server]:
    """Load and validate a JSON inventory file into :class:`Server` objects."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise click.ClickException("Inventory file must contain a JSON array.")
    try:
        return [Server.model_validate(item) for item in raw]
    except Exception as exc:  # pragma: no cover - surfaced to the user
        raise click.ClickException(f"Invalid inventory: {exc}") from exc


def _dump_servers(servers: list[Server], path: Path) -> None:
    """Serialize servers back to a JSON inventory file."""
    payload = [s.model_dump(mode="json") for s in servers]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="migration-factory")
@click.option("--log-level", default=None, help="Override the configured log level.")
@click.pass_context
def main(ctx: click.Context, log_level: str | None) -> None:
    """Assess, plan, and orchestrate cloud migrations."""
    settings = get_settings()
    configure_logging(log_level or settings.log_level, json_format=settings.log_json)
    ctx.obj = settings


@main.command()
@click.argument("inventory", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Write the assessed inventory to this JSON file.",
)
@click.pass_obj
def assess(settings, inventory: Path, output: Path | None) -> None:
    """Compute disposition recommendations for an INVENTORY file."""
    servers = _load_inventory(inventory)
    assessor = Assessor(idle_cpu_threshold=settings.idle_cpu_threshold)
    results = [assessor.assess_server(s) for s in servers]

    for result in results:
        click.echo(
            f"{result.server.id:<16} {result.server.disposition.value:<12} "
            f"readiness={result.readiness_score:>3}"
        )

    if output:
        _dump_servers(servers, output)
        click.echo(f"Wrote assessed inventory to {output}")


@main.command(name="plan-waves")
@click.argument("inventory", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--max-wave-size",
    type=int,
    default=None,
    help="Maximum number of servers per wave (defaults to configured value).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Write the planned inventory (with wave IDs) to this JSON file.",
)
@click.pass_obj
def plan_waves(
    settings, inventory: Path, max_wave_size: int | None, output: Path | None
) -> None:
    """Group assessed servers from INVENTORY into ordered migration waves."""
    servers = _load_inventory(inventory)
    # Assess first if the inventory has not been assessed yet.
    assessor = Assessor(idle_cpu_threshold=settings.idle_cpu_threshold)
    for server in servers:
        if server.disposition is None:
            assessor.assess_server(server)

    planner = WavePlanner(max_wave_size=max_wave_size or settings.max_wave_size)
    waves = planner.plan(servers)

    for wave in waves:
        click.echo(f"{wave.name}: {', '.join(wave.server_ids)}")

    if output:
        _dump_servers(servers, output)
        click.echo(f"Wrote planned inventory to {output}")


@main.command()
@click.argument("inventory", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--advance-to",
    type=click.Choice([s.value for s in TaskStatus]),
    default=TaskStatus.PENDING.value,
    help="Advance every task up to this status along the happy path.",
)
def status(inventory: Path, advance_to: str) -> None:
    """Create tasks for INVENTORY servers and report status counts."""
    servers = _load_inventory(inventory)
    orchestrator = MigrationOrchestrator()

    target = TaskStatus(advance_to)
    happy_path = [
        TaskStatus.PENDING,
        TaskStatus.REPLICATING,
        TaskStatus.TESTING,
        TaskStatus.CUTOVER,
        TaskStatus.COMPLETE,
    ]
    target_index = happy_path.index(target) if target in happy_path else 0

    for server in servers:
        task = orchestrator.create_task(server)
        while happy_path.index(task.status) < target_index:
            orchestrator.advance(task.id)

    for name, count in sorted(orchestrator.summary().items()):
        click.echo(f"{name:<12} {count}")


@main.command()
@click.argument("inventory", type=click.Path(exists=True, path_type=Path))
@click.pass_obj
def report(settings, inventory: Path) -> None:
    """Print a combined assessment and wave-plan summary for INVENTORY."""
    servers = _load_inventory(inventory)
    assessor = Assessor(idle_cpu_threshold=settings.idle_cpu_threshold)
    results = [assessor.assess_server(s) for s in servers]

    dispositions: dict[str, int] = {}
    for result in results:
        key = result.server.disposition.value
        dispositions[key] = dispositions.get(key, 0) + 1

    planner = WavePlanner(max_wave_size=settings.max_wave_size)
    waves = planner.plan(servers)
    avg_readiness = (
        round(sum(r.readiness_score for r in results) / len(results), 1)
        if results
        else 0.0
    )

    click.echo("Migration Factory Report")
    click.echo("=" * 40)
    click.echo(f"Servers assessed : {len(servers)}")
    click.echo(f"Average readiness: {avg_readiness}")
    click.echo(f"Waves planned    : {len(waves)}")
    click.echo("")
    click.echo("Dispositions:")
    for name, count in sorted(dispositions.items()):
        click.echo(f"  {name:<12} {count}")


if __name__ == "__main__":  # pragma: no cover
    main()
