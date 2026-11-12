import os
import sys
from urllib.error import HTTPError, URLError

from openai import OpenAIError

from analyze_failure import _ask_model, _http_error_details, _openai_error_details


def main() -> int:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY is not set in this shell.", file=sys.stderr)
        return 2

    model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
    try:
        response = _ask_model(
            "Explain the importance of fast language models.",
            "",
            api_key,
            model,
        )
    except OpenAIError as error:
        print(f"Groq request failed: {_openai_error_details(error)}", file=sys.stderr)
        return 1
    except HTTPError as error:
        print(f"Groq request failed: {_http_error_details(error)}", file=sys.stderr)
        return 1
    except URLError as error:
        print(f"Groq network request failed ({type(error.reason).__name__}).", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Groq request failed ({type(error).__name__}).", file=sys.stderr)
        return 1

    print(f"Groq API responded successfully. Model: {model}")
    print(f"Model response: {response}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
