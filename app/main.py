import json
import os

import fastapi

from app import database
from app.routers.main import router as main_router


class PrettyJSONResponse(fastapi.responses.JSONResponse):
    def render(self, content: object) -> bytes:
        """
        Serializes the given content to indented JSON bytes for the HTTP response.

        Args:
            content (object): The content to serialize as JSON.

        Returns:
            bytes: The UTF-8 encoded, indented JSON representation of content.
        """
        return json.dumps(content, indent=2, ensure_ascii=False).encode("utf-8")


def create_app(config_path: str = "config.ini") -> fastapi.FastAPI:
    """
    Creates and configures the FastAPI application instance.

    Initializes the database connection from the provided config file, attaches the
    session factory to application state, and registers the main router.

    The database is not created here. It must already exist and match the current
    schema; run `python -m app.populate_database` first. This keeps a stale or
    partial database file from being silently patched with new tables at startup.

    Args:
        config_path (str): The path to the application configuration file (default: "config.ini").

    Returns:
        fastapi.FastAPI: The configured FastAPI application instance.

    Raises:
        FileNotFoundError: If the configured database file does not exist.
    """
    app = fastapi.FastAPI(
        contact={
            "name": "MOAlmanac API GitHub",
            "url": "https://github.com/vanallenlab/moalmanac-api",
        },
        default_response_class=PrettyJSONResponse,
        description=(
            "The Molecular Oncology Almanac (MOAlmanac) is a paired knowledgebase and clinical interpretation "
            "algorithm for precision cancer medicine. Visit [our website](https://dev.moalmanac.org) for more "
            "information."
        ),
        docs_url="/",
        license_info={
            "name": "License: GNU GPL, Version 2",
            "url": "https://github.com/vanallenlab/moalmanac-api/blob/main/LICENSE",
        },
        openapi_tags=[
            {
                "name": "Service Info",
                "description": "Get metadata about the API service.",
            },
            {
                "name": "Search",
                "description": "Search across database records. Primarily uses /propositions endpoint with additional aggregated information.",
            },
            {
                "name": "Entities",
                "description": "Access to the database content.",
            },
        ],
        title="Molecular Oncology Almanac API",
        redoc_url=None,
        version="draft",
    )

    config = database.read_config_ini(path=config_path)
    database_path = config["database"]["path"]
    if not os.path.exists(database_path):
        raise FileNotFoundError(
            f"{database_path} does not exist. Run "
            "`python -m app.populate_database -i moalmanac-db/referenced -c "
            f"{config_path}` to create it.",
        )

    _, session_factory = database.init_db(config_path=config_path)

    app.state.session_factory = session_factory

    app.include_router(main_router)
    return app


app = create_app()
