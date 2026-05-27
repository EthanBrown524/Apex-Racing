from datetime import datetime, timedelta
from typing import Iterator
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
MODEL_ID = "ibm/granite-3-8b-instruct"
WATSONX_VERSION = "2024-05-31"

_cached_token: str | None = None
_token_fetched_at: datetime | None = None


def get_access_token() -> str:
    global _cached_token, _token_fetched_at

    if (
        _cached_token is not None
        and _token_fetched_at is not None
        and datetime.utcnow() - _token_fetched_at < timedelta(minutes=55)
    ):
        return _cached_token

    api_key = os.getenv("IBM_API_KEY")
    if not api_key:
        raise RuntimeError("IBM_API_KEY is not configured")

    response = httpx.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        timeout=30,
    )
    response.raise_for_status()

    _cached_token = response.json()["access_token"]
    _token_fetched_at = datetime.utcnow()
    return _cached_token


def generate(
    prompt: str,
    max_new_tokens: int = 500,
    temperature: float = 0.7,
    timeout: float = 60,
) -> str:
    project_id = os.getenv("WATSONX_PROJECT_ID")
    watsonx_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    if not project_id:
        raise RuntimeError("WATSONX_PROJECT_ID is not configured")

    token = get_access_token()
    url = f"{watsonx_url}/ml/v1/text/generation?version={WATSONX_VERSION}"

    payload = {
        "model_id": MODEL_ID,
        "project_id": project_id,
        "input": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
        },
    }

    response = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    return response.json()["results"][0]["generated_text"]


def generate_stream(
    prompt: str,
    max_new_tokens: int = 500,
    temperature: float = 0.7,
    timeout: float = 60,
) -> Iterator[str]:
    """Yield Granite text chunks via the watsonx streaming endpoint.

    Falls back to a single-yield non-streaming call when streaming is not
    available (older deployments, missing credentials) so callers never
    have to branch.
    """
    project_id = os.getenv("WATSONX_PROJECT_ID")
    watsonx_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    if not project_id:
        raise RuntimeError("WATSONX_PROJECT_ID is not configured")

    token = get_access_token()
    url = f"{watsonx_url}/ml/v1/text/generation_stream?version={WATSONX_VERSION}"

    payload = {
        "model_id": MODEL_ID,
        "project_id": project_id,
        "input": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
        },
    }

    try:
        with httpx.stream(
            "POST",
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            json=payload,
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines():
                if not raw_line:
                    continue
                line = raw_line if isinstance(raw_line, str) else raw_line.decode("utf-8")
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    continue
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                results = obj.get("results") or []
                for item in results:
                    text = item.get("generated_text")
                    if text:
                        yield text
    except httpx.HTTPError:
        # Fall back to a single non-streaming call so the UI still works
        # when watsonx returns 4xx/5xx on the streaming endpoint.
        text = generate(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            timeout=timeout,
        )
        if text:
            yield text
