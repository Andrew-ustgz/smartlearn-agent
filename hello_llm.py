import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv(".env", override=True)

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()

    if not api_key:
        print("Error: DEEPSEEK_API_KEY was not found in .env")
        sys.exit(1)

    client = OpenAI(
        base_url="https://api.deepseek.com",
        api_key=api_key,
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {
                    "role": "user",
                    "content": "What is Python in 2 sentences?",
                }
            ],
        )

        answer = response.choices[0].message.content

        print("\n===== DeepSeek Response =====")
        print(answer)

    except Exception as error:
        print("\n===== API Call Failed =====")
        print(f"{type(error).__name__}: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
