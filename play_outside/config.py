import pydantic
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from pydantic import Field
from typing import Any
from fastapi.templating import Jinja2Templates
from urllib.parse import quote_plus
from typing import Optional
from datetime import datetime
from datetime import timezone
from functools import lru_cache
import os
import jinja2

from rich.console import Console

console = Console()


class ApiServer(BaseModel):
    app: str = "play_outside.api:app"
    port: int = 8200
    reload: bool = True
    log_level: str = "info"
    host: str = "0.0.0.0"
    workers: int = 1
    forwarded_allow_ips: str = "*"
    proxy_headers: bool = True


if hasattr(jinja2, "pass_context"):
    pass_context = jinja2.pass_context
else:
    pass_context = jinja2.contextfunction


@pass_context
def https_url_for(context: dict, name: str, **path_params: Any) -> str:
    request = context["request"]
    http_url = request.url_for(name, **path_params)
    return str(http_url).replace("http", "https", 1)


def get_templates(config: BaseSettings) -> Jinja2Templates:
    templates = Jinja2Templates(directory="templates")
    templates.env.filters["quote_plus"] = lambda u: quote_plus(str(u))
    templates.env.filters["timestamp"] = lambda u: datetime.fromtimestamp(
        u, tz=timezone.utc
    ).strftime("%B %d, %Y")
    templates.env.globals["https_url_for"] = https_url_for
    templates.env.globals["config"] = config
    templates.env.globals["datetime"] = datetime
    templates.env.globals["len"] = len
    templates.env.globals["int"] = int
    console.print(f'Using environment: {os.environ.get("ENV")}')

    if os.environ.get("ENV") in ["dev", "qa", "prod"]:
        templates.env.globals["url_for"] = https_url_for
        console.print("Using HTTPS")
    else:
        console.print("Using HTTP")

    return templates


class Config(BaseSettings):
    env: str = "prod"
    open_weather_api_key: Optional[str] = None
    api_server: ApiServer = ApiServer()
    the_templates: Optional[Jinja2Templates] = Field(None, exclude=True)
    model_config = SettingsConfigDict(
        env_prefix="PLAY_OUTSIDE_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    @property
    def templates(self) -> Jinja2Templates:
        if self.the_templates is None:
            self.the_templates = get_templates(self)
        return self.the_templates

    @pydantic.validator("open_weather_api_key", pre=True, always=True)
    def validate_open_weather_api_key(cls, v):
        if v is None:
            v = os.getenv("OPEN_WEATHER_API_KEY")
        return v


@lru_cache
def get_config(env: Optional[str] = None):
    if env is None:
        env = os.environ.get("ENV", "prod")
    load_dotenv(dotenv_path=f".env.{env}")
    config = Config(env=env)
    return config
