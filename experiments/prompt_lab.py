import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(".env", override=True)

api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()

if not api_key:
    raise SystemExit(
        "DEEPSEEK_API_KEY is missing. Add it to .env and try again."
    )

client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key=api_key,
)


def ask(prompt: str) -> str:
    """Send one prompt to DeepSeek and return the answer text."""
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=600,
    )

    content = response.choices[0].message.content

    if not content:
        return "[No response content]"

    return content


# Level A: vague prompt
prompt_a = "Explain Python lists"

# Level B: role and constraint
prompt_b = (
    "You are a Python tutor for beginners. "
    "Explain Python lists in under 100 words."
)

# Level C: role, constraint, and output format
prompt_c = """You are a Python tutor for beginners. Explain Python lists.
Format:
1) One-sentence definition
2) Three common operations with code examples
3) One common mistake to avoid"""


def main() -> None:
    prompts = {
        "Level A (Vague)": prompt_a,
        "Level B (Structured)": prompt_b,
        "Level C (Precise)": prompt_c,
    }

    for level, prompt in prompts.items():
        print("\n" + "=" * 60)
        print(f"  {level}")
        print("=" * 60)
        print("Prompt:")
        print(prompt)
        print("-" * 60)

        try:
            answer = ask(prompt)
            print(answer)
        except Exception as error:
            print(f"API call failed: {type(error).__name__}: {error}")
            sys.exit(1)


if __name__ == "__main__":
    main()

