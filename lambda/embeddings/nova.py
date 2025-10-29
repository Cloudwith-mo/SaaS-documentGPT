"""Amazon Nova embedding client scaffolding."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import boto3


@dataclass(frozen=True)
class NovaEmbeddingRequest:
    """Information required to create Nova embeddings for a media asset."""

    user_id: str
    doc_id: str
    media_type: str
    s3_uri: str
    segments: Optional[Sequence[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    payload: Optional[bytes] = None


@dataclass(frozen=True)
class NovaEmbeddingResponse:
    """Response payload returned after embedding generation."""

    vectors: List[List[float]]
    model_id: str
    media_type: str
    metadata: Dict[str, Any]


class NovaEmbeddingClient:
    """Thin wrapper around the Bedrock runtime for Nova embeddings."""

    def __init__(
        self,
        *,
        region: str,
        model_id: str,
        role_arn: Optional[str] = None,
        boto3_session: Optional[boto3.session.Session] = None,
    ) -> None:
        if not region:
            raise ValueError("NovaEmbeddingClient requires a Bedrock region")
        if not model_id:
            raise ValueError("NovaEmbeddingClient requires a model identifier")

        self.region = region
        self.model_id = model_id
        self.role_arn = role_arn
        session = boto3_session or boto3.session.Session(region_name=region)
        self._client = session.client("bedrock-runtime")

    def embed(self, request: NovaEmbeddingRequest) -> NovaEmbeddingResponse:
        """Generate embeddings for the supplied media using Amazon Bedrock Nova."""

        payload_b64 = (
            base64.b64encode(request.payload).decode("utf-8")
            if request.payload is not None
            else None
        )

        body: Dict[str, Any] = {
            "input": {
                "mediaType": request.media_type,
            }
        }

        if payload_b64:
            body["input"]["data"] = payload_b64
        if request.segments:
            body["input"]["segments"] = list(request.segments)
        if request.metadata:
            body["metadata"] = request.metadata
        body["input"]["source"] = request.s3_uri

        response = self._client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )

        stream = response.get("body")
        if hasattr(stream, "read"):
            raw_payload = stream.read()
        else:
            raw_payload = stream or b"{}"
        if isinstance(raw_payload, bytes):
            decoded = json.loads(raw_payload.decode("utf-8"))
        else:
            decoded = json.loads(str(raw_payload))

        vectors = decoded.get("embeddings") or decoded.get("vectors") or []
        if not isinstance(vectors, list):
            raise RuntimeError("Nova response did not contain embeddings list")

        combined_metadata = {}
        if decoded.get("metadata"):
            combined_metadata.update(decoded["metadata"])
        if request.metadata:
            combined_metadata.update(request.metadata)

        return NovaEmbeddingResponse(
            vectors=vectors,
            model_id=self.model_id,
            media_type=request.media_type,
            metadata=combined_metadata,
        )


__all__ = ["NovaEmbeddingClient", "NovaEmbeddingRequest", "NovaEmbeddingResponse"]
