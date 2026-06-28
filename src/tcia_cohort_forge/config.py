from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    api_base_url: str = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4"
    auth_token: str | None = None
    output_dir: str = "downloads"
    request_timeout: int = 60
    max_retries: int = 3
    default_page_size: int = 50
    user_agent: str = "tcia-cohort-forge/0.1.0"

    def get_api_url(self, endpoint: str) -> str:
        base = self.api_base_url.rstrip("/")
        ep = endpoint.lstrip("/")
        return f"{base}/{ep}"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            api_base_url=os.environ.get(
                "TCIA_API_BASE_URL",
                "https://nbia.cancerimagingarchive.net/nbia-api/services/v4",
            ),
            auth_token=os.environ.get("TCIA_AUTH_TOKEN"),
            output_dir=os.environ.get("TCIA_OUTPUT_DIR", "downloads"),
            request_timeout=int(os.environ.get("TCIA_TIMEOUT", "60")),
        )
