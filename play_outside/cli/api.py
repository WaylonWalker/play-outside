from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from play_outside.config import get_config

api_app = typer.Typer()


@api_app.callback()
def api():
    "model cli"


@api_app.command()
def config(
    env: str = typer.Option(
        help="the environment to use",
    ),
):
    play_outside_config = get_config(env)
    Console().print(play_outside_config)


@api_app.command()
def upgrade(
    env: str = typer.Option(
        help="the environment to use",
    ),
    alembic_revision: str = typer.Option(
        "head",
        help="the alembic revision to use",
    ),
):
    play_outside_config = get_config(env)
    Console().print(play_outside_config)
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", play_outside_config.database_url)
    alembic.command.upgrade(config=alembic_cfg, revision=alembic_revision)


@api_app.command()
def revision(
    env: str = typer.Option(
        help="the environment to use",
    ),
    alembic_revision: str = typer.Option(
        "head",
        help="the alembic revision to upgrade to before creating a new revision",
    ),
    message: str = typer.Option(
        None,
        "--message",
        "-m",
        help="the message to use for the new revision",
    ),
):
    play_outside_config = get_config(env)
    Console().print(play_outside_config)
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", play_outside_config.database_url)
    alembic.command.upgrade(config=alembic_cfg, revision=alembic_revision)
    alembic.command.revision(
        config=alembic_cfg,
        message=message,
        autogenerate=True,
    )
    alembic.command.upgrade(config=alembic_cfg, revision="head")


@api_app.command()
def datasette(
    env: str = typer.Option(
        help="the environment to use",
    ),
    alembic_revision: str = typer.Option(
        "head",
        help="the alembic revision to use",
    ),
):
    from datasette.app import Datasette

    play_outside_config = get_config(env)
    Console().print(play_outside_config)
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", play_outside_config.database_url)
    alembic.command.upgrade(config=alembic_cfg, revision=alembic_revision)

    ds = Datasette(
        files=[Path(play_outside_config.database_url.replace("sqlite:///", ""))],
    )
    uvicorn.run(
        ds.app(), **play_outside_config.datasette_server.dict(exclude={"app", "reload"})
    )


@api_app.command()
def run(
    env: str = typer.Option(
        help="the environment to use",
    ),
    alembic_revision: str = typer.Option(
        "head",
        help="the alembic revision to use",
    ),
):
    play_outside_config = get_config(env)
    Console().print(play_outside_config)
    # alembic_cfg = Config("alembic.ini")
    # alembic_cfg.set_main_option("sqlalchemy.url", play_outside_config.database_url)
    # alembic.command.upgrade(config=alembic_cfg, revision=alembic_revision)
    uvicorn.run(**play_outside_config.api_server.dict())


@api_app.command()
def justrun(
    env: str = typer.Option(
        "local",
        help="the environment to use",
    ),
    alembic_revision: str = typer.Option(
        "head",
        help="the alembic revision to use",
    ),
):
    play_outside_config = get_config(env)
    Console().print(play_outside_config)
    uvicorn.run(**play_outside_config.api_server.dict())


if __name__ == "__main__":
    api_app()
