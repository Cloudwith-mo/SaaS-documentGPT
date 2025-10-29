"""Asynchronous media processing worker for DocumentGPT."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from pinecone import Pinecone

from config import get_settings
from embeddings import NovaEmbeddingClient, NovaEmbeddingRequest

settings = get_settings()

DOC_TABLE_NAME = settings.doc_table
PINECONE_API_KEY = settings.pinecone_api_key
PINECONE_INDEX_NAME = settings.pinecone_index or "documentgpt-dev"
BEDROCK_REGION = settings.bedrock_region or "us-east-1"
NOVA_MODEL_ID = settings.nova_embedding_model or "amazon.nova-embed-v1"
NOVA_ACCESS_ROLE_ARN = settings.nova_access_role_arn

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
docs_table = dynamodb.Table(DOC_TABLE_NAME)

pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pinecone_client.Index(PINECONE_INDEX_NAME)

nova_client = NovaEmbeddingClient(
    region=BEDROCK_REGION,
    model_id=NOVA_MODEL_ID,
    role_arn=NOVA_ACCESS_ROLE_ARN,
)


def lambda_handler(event, context):
    """Entry point for SQS-triggered media processing."""

    records: List[Dict[str, Any]] = event.get("Records", [])
    print(f"🧵 Processing {len(records)} media tasks")
    for record in records:
        try:
            job = json.loads(record.get("body") or "{}")
        except json.JSONDecodeError:
            print(f"⚠️ Invalid job payload: {record.get('body')}")
            continue

        try:
            _process_job(job)
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"❌ Media processing failed for job {job}: {exc}")
            _mark_document_failed(job, str(exc))


def _process_job(job: Dict[str, Any]) -> None:
    user_id = job["user_id"]
    doc_id = job["doc_id"]
    bucket = job["bucket"]
    key = job["key"]
    media_type = job.get("media_type", "application/octet-stream")
    metadata = job.get("metadata") or {}
    segments = job.get("segments") or []

    print(f"🎬 Embedding media for doc={doc_id} type={media_type}")

    obj = s3_client.get_object(Bucket=bucket, Key=key)
    payload = obj["Body"].read()

    request = NovaEmbeddingRequest(
        user_id=user_id,
        doc_id=doc_id,
        media_type=media_type,
        s3_uri=f"s3://{bucket}/{key}",
        segments=segments,
        metadata=metadata,
        payload=payload,
    )

    response = nova_client.embed(request)

    if not response.vectors:
        raise RuntimeError("Nova returned no embeddings")

    upserts = []
    for idx, vector in enumerate(response.vectors):
        vector_id = f"{doc_id}-{uuid4().hex[:8]}-{idx}"
        vector_metadata = {
            "doc_id": doc_id,
            "user_id": user_id,
            "media_type": media_type,
            **(response.metadata or {}),
        }
        upserts.append(
            {
                "id": vector_id,
                "values": vector,
                "metadata": vector_metadata,
            }
        )

    pinecone_index.upsert(vectors=upserts)
    print(f"📌 Upserted {len(upserts)} embeddings for {doc_id}")

    docs_table.update_item(
        Key={"pk": f"USER#{user_id}", "sk": f"DOC#{doc_id}"},
        UpdateExpression=(
            "SET processing_status = :ready, embedding_count = if_not_exists(embedding_count, :zero) + :count, "
            "updated_at = :ts"
        ),
        ExpressionAttributeValues={
            ":ready": "ready",
            ":zero": Decimal(0),
            ":count": Decimal(len(upserts)),
            ":ts": datetime.now(tz=timezone.utc).isoformat(),
        },
    )


def _mark_document_failed(job: Dict[str, Any], message: str) -> None:
    try:
        docs_table.update_item(
            Key={"pk": f"USER#{job.get('user_id')}", "sk": f"DOC#{job.get('doc_id')}"},
            UpdateExpression="SET processing_status = :failed, last_error = :error, updated_at = :ts",
            ExpressionAttributeValues={
                ":failed": "failed",
                ":error": message[:512],
                ":ts": datetime.now(tz=timezone.utc).isoformat(),
            },
        )
    except ClientError as err:  # pragma: no cover - defensive logging
        print(f"⚠️ Failed to mark document as failed: {err}")
