#!/usr/bin/env python3

import argparse
import sys
import urllib.request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether a web service responds.")
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Local service port to check.",
    )
    parser.add_argument(
        "--path",
        default="/",
        help="HTTP path to request. Defaults to /.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5,
        help="Request timeout in seconds.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    url = f"http://localhost:{args.port}{args.path}"

    print(f"[CHECK] Hitting {url}")

    try:
        with urllib.request.urlopen(url, timeout=args.timeout) as response:
            if response.status == 200:
                print("[OK] Service is responding")
                return 0

            print(f"[FAIL] Status {response.status}")
            return 1

    except Exception as error:
        print(f"[FAIL] {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())