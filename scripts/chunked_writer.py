#!/usr/bin/env python3
"""chunked_writer.py - Reliable large file generation for Hermes Agent.

Problem: write_file and execute_code have implicit content length limits.
When exceeded, content is silently truncated, leaving broken scripts.

Solution: Several strategies depending on your use case:
  1. write_large_file() - Append content in chunks using Python file I/O.
  2. write_large_binary() - Append base64 encoded binary data in chunks.
  3. serialize_data() + run_driver() - Split static data from driver logic.
  4. render_template() - Fill a compact template with data at runtime.
  5. replace_large_block() - Safe find-and-replace for large chunks.

Usage inside execute_code:
    import sys
    sys.path.insert(0, "/home/yash/.hermes/skills/software-development/chunked-code-generation/scripts")
    from chunked_writer import write_large_file
"""

import json
import os
import sys
import base64


# ---------------------------------------------------------------------------
# Strategy 1 & 2: Write raw text or binary files larger than tool limits
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

def write_large_binary(path: str, base64_content: str, chunk_size: int = 12000):
    """Write binary content to path in chunks from a base64 string."""
    with open(path, "wb") as f:
        f.write(b"")
    
    raw_bytes = base64.b64decode(base64_content)
    offset = 0
    total = len(raw_bytes)
    while offset < total:
        chunk = raw_bytes[offset:offset + chunk_size]
        with open(path, "ab") as f:
            f.write(chunk)
        offset += chunk_size
        
    written = os.path.getsize(path)
    print(f"[chunked_writer] Wrote {written} binary bytes to {path}")
    return written


# ---------------------------------------------------------------------------
# Strategy 3: Safe find-and-replace for large edits (bypass `patch` limits)
# ---------------------------------------------------------------------------

def replace_large_block(path: str, old_string: str, new_string: str, chunk_size: int = 12000):
    """A Hermes patch alternative for huge replacements.
    Reads full file, does the replace, and uses write_large_file to save it."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if old_string not in content:
        print(f"[chunked_writer] old_string not found in {path}")
        return False
        
    content = content.replace(old_string, new_string)
    write_large_file(path, content, chunk_size)
    return True


# ---------------------------------------------------------------------------
# Strategy 4: Serialize data + run a compact driver
# ---------------------------------------------------------------------------

def serialize_data(path: str, data, pretty: bool = True):
    """Save dict/list data to JSON for a driver script to consume."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2 if pretty else None, default=str, ensure_ascii=False)
    print(f"[chunked_writer] Serialized {len(str(data))} chars to {path}")

def run_driver(driver_script_path: str, data_path: str, output_path: str = None, extra_vars: dict = None):
    """Execute a compact driver script that reads serialized data."""
    cmd_parts = [sys.executable, driver_script_path, data_path]
    if output_path:
        cmd_parts.append(output_path)
    if extra_vars:
        cmd_parts.append(json.dumps(extra_vars))
    os.system(" ".join(cmd_parts))


# ---------------------------------------------------------------------------
# Strategy 5: Lightweight template rendering
# ---------------------------------------------------------------------------

def render_template(template_path: str, data: dict, output_path: str,
                    placeholder_fmt: str = "{{{{{{{key}}}}}"):
    """Simple variable substitution. No Jinja2 dependency."""
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

def detect_write_limit(test_path: str = "/tmp/_chunked_limit_test.txt", test_sizes=None):
    """Test different write sizes to find the tool's truncation ceiling."""
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
    p_write.add_argument("--content-file", help="Path to a file containing the full content (or '-' for stdin)")
    p_write.add_argument("--chunk-size", type=int, default=12000)

    p_write_bin = sub.add_parser("write_binary", help="Write large binary file from base64 chunks")
    p_write_bin.add_argument("--path", required=True)
    p_write_bin.add_argument("--content-file", help="Path to a file containing base64 content (or '-' for stdin)")
    p_write_bin.add_argument("--chunk-size", type=int, default=12000)

    p_replace = sub.add_parser("replace", help="Replace large block without tool truncation")
    p_replace.add_argument("--path", required=True)
    p_replace.add_argument("--old-file", required=True, help="Path to file containing old string")
    p_replace.add_argument("--new-file", required=True, help="Path to file containing new string")

    p_serialize = sub.add_parser("serialize", help="Serialize data to JSON")
    p_serialize.add_argument("--path", required=True)
    p_serialize.add_argument("--data-file", required=True)

    p_render = sub.add_parser("render", help="Render template with data")
    p_render.add_argument("--template", required=True)
    p_render.add_argument("--data", required=True)
    p_render.add_argument("--output", required=True)

    p_detect = sub.add_parser("detect", help="Detect tool write limit")

    args = parser.parse_args()

    def get_content(arg_val):
        if arg_val == '-':
            return sys.stdin.read()
        with open(arg_val, "r", encoding="utf-8") as f:
            return f.read()

    if args.cmd == "write":
        content = get_content(args.content_file) if args.content_file else sys.stdin.read()
        write_large_file(args.path, content, args.chunk_size)
    elif args.cmd == "write_binary":
        content = get_content(args.content_file) if args.content_file else sys.stdin.read()
        write_large_binary(args.path, content, args.chunk_size)
    elif args.cmd == "replace":
        old_str = get_content(args.old_file)
        new_str = get_content(args.new_file)
        success = replace_large_block(args.path, old_str, new_str)
        sys.exit(0 if success else 1)
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
