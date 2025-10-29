import os
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings, make_cors_headers, resolve_cors_origin


REQUIRED_ENV = {
    "OPENAI_API_KEY": "test-openai",
    "PINECONE_API_KEY": "test-pinecone",
    "PINECONE_INDEX_HOST": "test-host",
}


class SettingsTests(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_get_settings_populates_expected_fields(self) -> None:
        env = {
            **REQUIRED_ENV,
            "ALLOWED_ORIGINS": "https://example.com, https://foo.com",
            "ADD_ORIGIN_HEADER": "true",
            "DOC_TABLE": "custom-doc-table",
            "PINECONE_INDEX": "custom-index",
            "BEDROCK_REGION": "us-east-1",
            "NOVA_EMBEDDING_MODEL": "amazon.nova-embed-v1",
            "NOVA_ACCESS_ROLE_ARN": "arn:aws:iam::123456789012:role/NovaAccess",
            "DEFAULT_MODEL_ID": "gpt-4.1",
            "MEDIA_BUCKET": "docgpt-media-dev",
            "MEDIA_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789012/docgpt-media-queue",
        }

        with mock.patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            settings = get_settings()

        self.assertEqual(settings.openai_api_key, "test-openai")
        self.assertEqual(settings.pinecone_api_key, "test-pinecone")
        self.assertEqual(settings.pinecone_index_host, "test-host")
        self.assertEqual(settings.allowed_origins, ["https://example.com", "https://foo.com"])
        self.assertTrue(settings.add_origin_header)
        self.assertEqual(settings.doc_table, "custom-doc-table")
        self.assertEqual(settings.pinecone_index, "custom-index")
        self.assertEqual(settings.bedrock_region, "us-east-1")
        self.assertEqual(settings.nova_embedding_model, "amazon.nova-embed-v1")
        self.assertEqual(settings.nova_access_role_arn, "arn:aws:iam::123456789012:role/NovaAccess")
        self.assertEqual(settings.default_model_id, "gpt-4.1")
        self.assertEqual(settings.media_bucket, "docgpt-media-dev")
        self.assertEqual(settings.media_queue_url, "https://sqs.us-east-1.amazonaws.com/123456789012/docgpt-media-queue")

    def test_get_settings_requires_openai_api_key(self) -> None:
        env = {
            "PINECONE_API_KEY": "test-pinecone",
            "PINECONE_INDEX_HOST": "test-host",
        }

        with mock.patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            with self.assertRaises(RuntimeError):
                get_settings()

    def test_resolve_cors_origin_prefers_allowed_match(self) -> None:
        env = {
            **REQUIRED_ENV,
            "ALLOWED_ORIGINS": "https://example.com,https://foo.com",
        }

        with mock.patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            settings = get_settings()

        matched_origin = resolve_cors_origin(settings, {"Origin": "https://foo.com"})
        fallback_origin = resolve_cors_origin(settings, {"Origin": "https://not-allowed.com"})

        self.assertEqual(matched_origin, "https://foo.com")
        self.assertEqual(fallback_origin, "https://example.com")

    def test_make_cors_headers_includes_expected_values(self) -> None:
        env = {
            **REQUIRED_ENV,
            "ALLOWED_ORIGINS": "https://example.com,https://foo.com",
            "ADD_ORIGIN_HEADER": "true",
        }

        with mock.patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            settings = get_settings()

        headers = make_cors_headers(settings, {"Origin": "https://foo.com"}, add_origin_header=True)

        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "https://foo.com")
        self.assertEqual(headers.get("Access-Control-Allow-Credentials"), "true")
        self.assertEqual(headers.get("Content-Type"), "application/json")

    def test_make_cors_headers_handles_wildcard_origins(self) -> None:
        env = {
            **REQUIRED_ENV,
            "ALLOWED_ORIGINS": "*",
            "ADD_ORIGIN_HEADER": "true",
        }

        with mock.patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            settings = get_settings()

        headers = make_cors_headers(settings, {"Origin": "https://other.com"})

        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "https://other.com")
        self.assertEqual(headers.get("Access-Control-Allow-Credentials"), "false")

    def test_make_cors_headers_respects_disabled_origin_header(self) -> None:
        env = {
            **REQUIRED_ENV,
            "ALLOWED_ORIGINS": "https://example.com",
            "ADD_ORIGIN_HEADER": "false",
        }

        with mock.patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            settings = get_settings()

        headers = make_cors_headers(settings, {})

        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_make_cors_headers_sets_vary_header_when_requested(self) -> None:
        env = {
            **REQUIRED_ENV,
            "ALLOWED_ORIGINS": "https://example.com",
        }

        with mock.patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            settings = get_settings()

        headers = make_cors_headers(settings, {}, vary_origin=True, add_origin_header=False)

        self.assertEqual(headers.get("Vary"), "Origin")
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_make_cors_headers_allows_explicit_credential_override(self) -> None:
        env = {
            **REQUIRED_ENV,
            "ALLOWED_ORIGINS": "https://example.com",
            "ADD_ORIGIN_HEADER": "true",
        }

        with mock.patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            settings = get_settings()

        headers = make_cors_headers(
            settings,
            {"Origin": "https://example.com"},
            include_credentials=False,
        )

        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "https://example.com")
        self.assertEqual(headers.get("Access-Control-Allow-Credentials"), "false")


if __name__ == "__main__":
    unittest.main()
