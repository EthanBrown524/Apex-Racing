from dataclasses import dataclass
from datetime import datetime, timedelta
import os

import httpx
from dotenv import load_dotenv


load_dotenv()

TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
MODEL_ID = "ibm/granite-13b-chat-v2"
WATSONX_VERSION = "2023-05-29"


@dataclass
class GraniteClient:
    api_key: str | None = os.getenv("IBM_API_KEY")
    project_id: str | None = os.getenv("WATSONX_PROJECT_ID")
    watsonx_url: str = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    access_token: str | None = None
    token_fetched_at: datetime | None = None

    def _token_is_fresh(self) -> bool:
        if self.access_token is None or self.token_fetched_at is None:
            return False
        return datetime.utcnow() - self.token_fetched_at < timedelta(minutes=55)

    async def _refresh_token(self) -> None:
        if not self.api_key:
            raise RuntimeError("IBM_API_KEY is not configured")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self.api_key,
                },
            )
            response.raise_for_status()

        self.access_token = response.json()["access_token"]
        self.token_fetched_at = datetime.utcnow()

    async def generate(self, prompt: str, max_new_tokens: int = 500, temperature: float = 0.7) -> str:
        if not self.project_id:
            raise RuntimeError("WATSONX_PROJECT_ID is not configured")
        if not self._token_is_fresh():
            await self._refresh_token()

        url = f"{self.watsonx_url}/ml/v1/text/generation?version={WATSONX_VERSION}"
        payload = {
            "model_id": MODEL_ID,
            "project_id": self.project_id,
            "input": prompt,
            "parameters": {"max_new_tokens": max_new_tokens, "temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()

        result = response.json()
        return result["results"][0]["generated_text"]

