import asyncio
import json
import logging

import httpx
from httpx import AsyncClient, HTTPStatusError

from backend.core.config import settings
from backend.schemas.dify_response import ActionItemOutput, DifyResponse

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2

_TRANSIENT_EXCEPTIONS = (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError)


def _try_parse_json(value):
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str) and value.strip():
        trimmed = value.strip()
        if trimmed.startswith("[") or trimmed.startswith("{"):
            try:
                return json.loads(trimmed)
            except (json.JSONDecodeError, ValueError):
                logger.warning(f"Failed to parse JSON string: {trimmed[:100]}")
    return value


class DifyClient:
    def __init__(self):
        self.base_url = settings.dify_api_url.rstrip("/")
        self.api_key = settings.dify_api_key
        self.workflow_id = settings.dify_workflow_id
        self.client = AsyncClient(timeout=60.0)

    async def run_workflow(self, text: str, source_type: str = "text") -> dict:
        if not self.api_key:
            raise ValueError("DIFY_API_KEY is not configured")

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                result = await self._call_dify(text, source_type)
                return result
            except _TRANSIENT_EXCEPTIONS as e:
                last_error = e
                logger.warning(f"Dify API call attempt {attempt + 1}/{MAX_RETRIES} failed (transient): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            except HTTPStatusError as e:
                if e.response.status_code >= 500:
                    last_error = e
                    logger.warning(f"Dify API call attempt {attempt + 1}/{MAX_RETRIES} failed (server error): {e}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    raise

        raise RuntimeError(f"Dify API failed after {MAX_RETRIES} retries: {last_error}")

    async def _call_dify(self, text: str, source_type: str) -> dict:
        url = f"{self.base_url}/workflows/run"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": {
                "input_text": text,
                "source_type": source_type,
            },
            "response_mode": "blocking",
            "user": "info-butler",
        }

        if self.workflow_id:
            payload["workflow_id"] = self.workflow_id

        resp = await self.client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        raw_output = data.get("data", {}).get("outputs", {})
        logger.info(f"Dify raw_output keys: {list(raw_output.keys())}")

        return self._normalize_output(raw_output)

    def _normalize_output(self, raw_output: dict) -> dict:
        summary = raw_output.get("summary", "")
        if isinstance(summary, list):
            summary = " ".join(str(s) for s in summary)

        tags_raw = raw_output.get("tags", [])
        tags_raw = _try_parse_json(tags_raw)
        if isinstance(tags_raw, str):
            tags_raw = [t.strip() for t in tags_raw.split(",") if t.strip()]
        tags = [str(t) for t in tags_raw if t]

        action_items_raw = raw_output.get("action_items", [])
        action_items_raw = _try_parse_json(action_items_raw)
        action_items_processed = []
        for item in action_items_raw:
            if isinstance(item, dict):
                content = item.get("content", "").strip()
                priority = item.get("priority", "medium")
                if content:
                    action_items_processed.append({"content": content, "priority": priority})
            elif isinstance(item, str) and item.strip():
                action_items_processed.append({"content": item.strip(), "priority": "medium"})

        return {
            "summary": str(summary).strip(),
            "action_items": action_items_processed,
            "tags": tags,
        }

    def validate_response(self, data: dict) -> DifyResponse | None:
        try:
            action_items_data = []
            for item in data.get("action_items", []):
                if isinstance(item, dict):
                    action_items_data.append(ActionItemOutput(**item))
                else:
                    action_items_data.append(ActionItemOutput(content=str(item), priority="medium"))

            tags = data.get("tags", [])
            summary = data.get("summary", "") or ""

            return DifyResponse(
                summary=summary,
                action_items=action_items_data[:3],
                tags=tags[:5],
            )
        except Exception as e:
            logger.warning(f"Dify response validation failed: {e}")
            return None

    async def close(self):
        await self.client.aclose()


dify_client = DifyClient()
