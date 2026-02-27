import httpx
import os
import asyncio
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()


async def test_featherless_connection():
    api_key = os.getenv("FEATHERLESS_API_KEY")
    base_url = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
    model_name = "Qwen/Qwen3-0.6B"  # Using your preferred model

    if not api_key:
        print("❌ Error: FEATHERLESS_API_KEY not found in .env file.")
        return

    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Payload similar to your curl request
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hello, are you working?"}],
        "max_tokens": 50,
    }

    print(f"Testing connection to {url}...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=headers, json=payload, timeout=10.0
            )

            # Raise exception for 4XX/5XX responses
            response.raise_for_status()

            print("✅ Connection Successful!")
            print("Response:", response.json()["choices"][0]["message"]["content"])

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(test_featherless_connection())
