import fastapi
import json

from app import database
from app import models
from app.routers.main import router as main_router


class PrettyJSONResponse(fastapi.responses.JSONResponse):
    def render(self, content: object) -> bytes:
        return json.dumps(content, indent=2, ensure_ascii=False).encode("utf-8")


def create_app(config_path: str = "config.ini") -> fastapi.FastAPI:
    app = fastapi.FastAPI(
        contact={
            "name": "MOAlmanac API GitHub",
            "url": "https://github.com/vanallenlab/moalmanac-api",
        },
        default_response_class=fastapi.responses.ORJSONResponse,
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
                "name": "Entities",
                "description": "Access to the database content.",
            },
            {
                "name": "Service Info",
                "description": "Metadata about the API service.",
            },
        ],
        title="Molecular Oncology Almanac API",
        redoc_url=None,
        version="draft",
    )

    engine, session_factory = database.init_db(config_path=config_path)
    models.Base.metadata.create_all(bind=engine)

    app.state.session_factory = session_factory

    app.include_router(main_router)
    return app


app = create_app()
