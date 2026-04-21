import logging

from httpx import AsyncClient

from backend.core.config import settings
from backend.schemas.dify_response import ActionItemOutput, DifyResponse

logger = logging.getLogger(__name__)


class DifyClient:
    def __init__(self):
        self.base_url = settings.dify_api_url.rstrip("/")
        self.api_key = settings.dify_api_key
        self.workflow_id = settings.dify_workflow_id
        self.client = AsyncClient(timeout=60.0)

    async def run_workflow(self, text: str, source_type: str = "text") -> dict:
        if not self.api_key:
            raise ValueError("DIFY_API_KEY is not configured")

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

        try:
            resp = await self.client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            raw_output = data.get("data", {}).get("outputs", {})
            logger.info(f"Dify raw_output: {raw_output}")

            action_items_raw = raw_output.get("action_items", [])
            action_items_processed = []
            for item in action_items_raw:
                if isinstance(item, dict):
                    action_items_processed.append(
                        {"content": item.get("content", ""), "priority": item.get("priority", "medium")}
                    )
                elif isinstance(item, str):
                    action_items_processed.append({"content": item, "priority": "medium"})

            return {
                "summary": raw_output.get("summary", ""),
                "action_items": action_items_processed,
                "tags": raw_output.get("tags", []),
            }
        except Exception as e:
            logger.error(f"Dify API call failed: {e}")
            raise

    def validate_response(self, data: dict) -> DifyResponse | None:
        try:
            action_items_data = []
            for item in data.get("action_items", []):
                if isinstance(item, dict):
                    action_items_data.append(ActionItemOutput(**item))
                else:
                    action_items_data.append(ActionItemOutput(content=str(item), priority="medium"))

            return DifyResponse(
                summary=data.get("summary", ""),
                action_items=action_items_data,
                tags=data.get("tags", []),
            )
        except Exception as e:
            logger.warning(f"Dify response validation failed: {e}")
            return None

    async def close(self):
        await self.client.aclose()


dify_client = DifyClient()
