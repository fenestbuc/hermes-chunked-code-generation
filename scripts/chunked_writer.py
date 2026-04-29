#!/usr/bin/env python3
"""chunked_writer.py - Reliable large file generation for Hermes Agent.

Problem: write_file and execute_code have implicit content length limits.
When exceeded, content is silently truncated, leaving broken scripts.

Solution: Three strategies depending on your use case:
  1. write_large_file() - Append content in chunks using Python file I/O.
  2. serialize_data() + run_driver() - Split static data from driver logic.
  3. render_template() - Fill a compact template with data at runtime.

Usage inside execute_code:
    from hermes_tools import terminal
    terminal("python3 ~/.hermes/skills/software-development/chunked-code-generation/scripts/chunked_writer.py ...")

Or import directly in your execute_code scripts.
"""

import json
import os
import sys


# ---------------------------------------------------------------------------
# Strategy 1: Write raw text files larger than tool limits
# ---------------------------------------------------------------------------

def write_large_file(path: str, content: str, chunk_size: int = 12000):
    """Write content to path in chunks to avoid tool truncation.

    chunk_size defaults to 12000 chars (safe under observed ~15K limit).
    Each chunk is written via a separate Python file operation.
    """
    # Clear file first
    with open(path, "w", encoding="utf-8") as f:
        f.write("")

    offset = 0
    total = len(content)
    while offset < total:
        chunk = content[offset:offset + chunk_size]
        with open(path, "a", encoding="utf-8") as f:
            f.write(chunk)
        offset += chunk_size

    written = os.path.getsize(path)
    print(f"[chunked_writer] Wrote {written} bytes to {path} ({total} chars)")
    return written


# ---------------------------------------------------------------------------
# Strategy 2: Serialize data + run a compact driver
# ---------------------------------------------------------------------------

def serialize_data(path: str, data, pretty: bool = True):
    """Save dict/list data to JSON for a driver script to consume.

    This avoids embedding large data literals in the script itself.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2 if pretty else None, default=str, ensure_ascii=False)
    print(f"[chunked_writer] Serialized {len(str(data))} chars to {path}")


def run_driver(driver_script_path: str, data_path: str, output_path: str = None,
               extra_vars: dict = None):
    """Execute a compact driver script that reads serialized data.

    The driver script should import json and load data_path.
    output_path and extra_vars are passed as CLI args for flexibility.
    """
    cmd_parts = [sys.executable, driver_script_path, data_path]
    if output_path:
        cmd_parts.append(output_path)
    if extra_vars:
        cmd_parts.append(json.dumps(extra_vars))
    os.system(" ".join(cmd_parts))


# ---------------------------------------------------------------------------
# Strategy 3: Lightweight template rendering
# ---------------------------------------------------------------------------

def render_template(template_path: str, data: dict, output_path: str,
                    placeholder_fmt: str = "{{{{{{{key}}}}}"):
    """Simple variable substitution. No Jinja2 dependency.

    placeholder_fmt uses triple braces by default to avoid collision with
    JSON or Python f-strings. Example: {{{name}}} -> 'Vaibhav'
    """
    with open(template_path, "r", encoding="utf-8") as f:
        text = f.read()

    for key, val in data.items():
        ph = placeholder_fmt.format(key=key)
        text = text.replace(ph, str(val))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"[chunked_writer] Rendered {len(text)} chars to {output_path}")
    return len(text)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def detect_write_limit(test_path: str = "/tmp/_chunked_limit_test.txt",
                       test_sizes=None):
    """Test different write sizes to find the tool's truncation ceiling.

    Returns the largest size that wrote successfully.
    """
    if test_sizes is None:
        test_sizes = [5000, 10000, 15000, 20000, 30000, 50000]

    results = {}
    for size in test_sizes:
        content = "X" * size
        try:
            write_large_file(test_path, content)
            actual = os.path.getsize(test_path)
            results[size] = actual
            if actual == size:
                print(f"  OK: {size} chars -> {actual} bytes")
            else:
                print(f"  TRUNCATED: {size} chars -> {actual} bytes")
                break
        except Exception as e:
            results[size] = f"ERROR: {e}"
            print(f"  FAILED: {size} chars -> {e}")
            break
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    return results


# ---------------------------------------------------------------------------
# CLI entrypoints (for terminal() invocation from skills)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Chunked file writer for Hermes")
    sub = parser.add_subparsers(dest="cmd")

    p_write = sub.add_parser("write", help="Write large file in chunks")
    p_write.add_argument("--path", required=True)
    p_write.add_argument("--content-file", required=True,
                         help="Path to a file containing the full content")
    p_write.add_argument("--chunk-size", type=int, default=12000)

    p_serialize = sub.add_parser("serialize", help="Serialize data to JSON")
    p_serialize.add_argument("--path", required=True)
    p_serialize.add_argument("--data-file", required=True,
                             help="Path to JSON file to serialize")

    p_render = sub.add_parser("render", help="Render template with data")
    p_render.add_argument("--template", required=True)
    p_render.add_argument("--data", required=True)
    p_render.add_argument("--output", required=True)

    p_detect = sub.add_parser("detect", help="Detect tool write limit")

    args = parser.parse_args()

    if args.cmd == "write":
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()
        write_large_file(args.path, content, args.chunk_size)
    elif args.cmd == "serialize":
        with open(args.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        serialize_data(args.path, data)
    elif args.cmd == "render":
        with open(args.data, "r", encoding="utf-8") as f:
            data = json.load(f)
        render_template(args.template, data, args.output)
    elif args.cmd == "detect":
        detect_write_limit()
    else:
        parser.print_help()
