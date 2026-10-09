import json
import sys
import uuid

from pydantic import BaseModel, Field, PrivateAttr


class SiteConfiguration(BaseModel):
    """Site configuration model."""

    host: str = Field(..., title="Server url")
    name: str = Field(..., title="Site name")
    title: str | None = Field(None, title="Site title")
    token: str | None = Field(None, title="Access token")


class FireflyConfig(BaseModel):
    """Firefly configuration model."""

    client_id: str = Field(default_factory=lambda: str(uuid.uuid1()), title="Client ID")
    debug: bool = Field(False, title="Debug mode")

    sites: list[SiteConfiguration] = Field(
        default_factory=list,
        title="Available sites",
    )

    _site: SiteConfiguration | None = PrivateAttr(None)

    @property
    def site(self) -> SiteConfiguration:
        """Current site. Selected at startup, before anything connects."""
        if self._site is None:
            raise RuntimeError("No site selected")
        return self._site

    def set_site(self, index: int) -> None:
        """Set current site."""
        self._site = self.sites[index]


def get_config() -> FireflyConfig:
    """Get firefly configuration."""

    try:
        with open("settings.json") as f:
            return FireflyConfig(**json.load(f))
    except Exception as e:
        # logging is not available yet: it depends on the configuration
        print(f"Failed to load configuration: {e}", file=sys.stderr)  # noqa: T201

    # Default configuration
    sites = [
        SiteConfiguration(name="nebula", host="http://localhost:4455"),
    ]

    return FireflyConfig(sites=sites)


config = get_config()
