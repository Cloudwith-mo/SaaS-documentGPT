"""Centralised configuration handling for the Lambda runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Mapping


def _get_env(name: str, default: str | None = None) -> str:
    """Fetch an environment variable, raising if it is missing."""

    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable '{name}' is required")
    return value


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    openai_api_key: str
    pinecone_api_key: str
    pinecone_index_host: str
    allowed_origins: List[str]
    add_origin_header: bool
    doc_table: str
    pinecone_index: str | None
    bedrock_region: str | None
    nova_embedding_model: str | None
    nova_access_role_arn: str | None
    default_model_id: str | None
    media_bucket: str | None
    media_queue_url: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once and reuse across invocations."""

    allowed = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
    if not allowed:
        allowed = ["*"]

    return Settings(
        openai_api_key=_get_env("OPENAI_API_KEY"),
        pinecone_api_key=_get_env("PINECONE_API_KEY"),
        pinecone_index_host=_get_env("PINECONE_INDEX_HOST"),
        allowed_origins=allowed,
        add_origin_header=os.environ.get("ADD_ORIGIN_HEADER", "false").lower() == "true",
        doc_table=os.environ.get("DOC_TABLE", "docgpt"),
        pinecone_index=os.environ.get("PINECONE_INDEX"),
        bedrock_region=os.environ.get("BEDROCK_REGION"),
        nova_embedding_model=os.environ.get("NOVA_EMBEDDING_MODEL"),
        nova_access_role_arn=os.environ.get("NOVA_ACCESS_ROLE_ARN"),
        default_model_id=os.environ.get("DEFAULT_MODEL_ID"),
        media_bucket=os.environ.get("MEDIA_BUCKET"),
        media_queue_url=os.environ.get("MEDIA_QUEUE_URL"),
    )


def resolve_cors_origin(settings: Settings, request_headers: Mapping[str, str] | None = None) -> str:
    """Determine the origin to echo in CORS responses."""

    headers = request_headers or {}
    request_origin = headers.get("origin") or headers.get("Origin")

    allowed = settings.allowed_origins or ["*"]
    explicit_origins = [origin for origin in allowed if origin != "*"]
    wildcard_allowed = "*" in allowed

    if request_origin:
        if request_origin in explicit_origins:
            return request_origin
        if wildcard_allowed:
            return request_origin

    if explicit_origins:
        return explicit_origins[0]

    return "*"


def make_cors_headers(
    settings: Settings,
    request_headers: Mapping[str, str] | None = None,
    *,
    content_type: str = "application/json",
    allow_headers: str = "Content-Type,Authorization,x-api-key,x-user-id,x-docgpt-state",
    allow_methods: str = "GET,POST,OPTIONS",
    add_origin_header: bool | None = None,
    include_credentials: bool | None = None,
    send_wildcard_credentials: bool = True,
    vary_origin: bool = False,
) -> dict[str, str]:
    """Build a CORS header set driven by shared settings."""

    allowed = settings.allowed_origins or ["*"]
    explicit_origins = [origin for origin in allowed if origin != "*"]
    origin = resolve_cors_origin(settings, request_headers)
    is_explicit_origin = origin in explicit_origins

    headers: dict[str, str] = {
        "Content-Type": content_type,
        "Access-Control-Allow-Headers": allow_headers,
        "Access-Control-Allow-Methods": allow_methods,
    }

    if vary_origin:
        headers["Vary"] = "Origin"

    include_origin_header = settings.add_origin_header if add_origin_header is None else add_origin_header

    if include_origin_header:
        headers["Access-Control-Allow-Origin"] = origin

        if include_credentials is None:
            if is_explicit_origin:
                headers["Access-Control-Allow-Credentials"] = "true"
            elif send_wildcard_credentials:
                headers["Access-Control-Allow-Credentials"] = "false"
        else:
            headers["Access-Control-Allow-Credentials"] = "true" if include_credentials else "false"

    return headers
