# chunked-code-generation v2

A Hermes Agent skill for reliably generating large files when tool-level content truncation silently corrupts your work.

## The Problem

Hermes `write_file` and `execute_code` have implicit character limits. On Cloudflare Workers AI / Kimi K-2.6, `write_file` truncates around **15,000 characters**. The model context window itself is 262K, but the tool layer silently cuts you off.

Result: broken scripts, missing closing tags, incomplete data, wasted debugging time.

## The Solution

Five strategies, one skill:

1. **Chunked File Write (Text)** — Write raw text >15K chars in chunks via Python I/O
2. **Chunked File Write (Binary)** — Write binary files via base64 encoded chunks
3. **Safe Find-And-Replace** — Bypass `patch` limits for big replacements
4. **Data Separation + Driver** — Split static data (JSON) from generation logic
5. **Template Rendering** — Fill compact templates with data at runtime

## Quick Start

```python
# Strategy 1: Write a 50K-char file without truncation
import sys
sys.path.insert(0, "~/.hermes/skills/software-development/chunked-code-generation/scripts")
from chunked_writer import write_large_file

write_large_file("output.sql", large_content, chunk_size=12000)

# Strategy 2: Generate a PDF report (data separate from logic)
python3 examples/generate_pdf_report.py --save-data
python3 examples/generate_pdf_report.py --output report.pdf

# Strategy 5: Render a static HTML site
python3 examples/generate_static_site.py --out ./site
```

## CLI Usage (New in v2)

You can pipe data directly to the writer script via stdin:
```bash
cat large_data.json | python3 scripts/chunked_writer.py write --path output.json --content-file -
```

## Diagnostics

Detect your current provider's truncation limit:

```bash
python3 scripts/chunked_writer.py detect
```

## When to Use Which Strategy

| Scenario | Strategy | Why |
|---|---|---|
| Large text file (SQL, markdown, YAML) | Chunked write | Direct file I/O avoids tool limits |
| Binary payload (PDF, image via base64) | Chunked binary | Translates model base64 safely to disk |
| Large string find-and-replace | Safe Replace | Bypasses `patch` limits on massive objects |
| PDF / report with tables and data | Data + driver | Data JSON can be huge; driver stays compact |
| HTML landing page with variables | Template render | Reusable template, dynamic data injection |
| Multi-file project scaffold | Data + driver | One data file drives many outputs |

## License

MIT
