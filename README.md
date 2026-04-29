# chunked-code-generation

A Hermes Agent skill for reliably generating large files when tool-level content truncation silently corrupts your work.

## The Problem

Hermes `write_file` and `execute_code` have implicit character limits. On Cloudflare Workers AI / Kimi K-2.6, `write_file` truncates around **15,000 characters**. The model context window itself is 262K, but the tool layer silently cuts you off.

Result: broken scripts, missing closing tags, incomplete data, wasted debugging time.

## The Solution

Three strategies, one skill:

1. **Chunked File Write** — Write raw text >15K chars in chunks via Python I/O
2. **Data Separation + Driver** — Split static data (JSON) from generation logic
3. **Template Rendering** — Fill compact templates with data at runtime

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

# Strategy 3: Render a static HTML site
python3 examples/generate_static_site.py --out ./site
```

## Files

```
SKILL.md                          # Full skill reference
scripts/chunked_writer.py         # Core helper library
examples/generate_pdf_report.py   # PDF generation example
examples/generate_static_site.py  # HTML site generation example
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
| PDF / report with tables and data | Data + driver | Data JSON can be huge; driver stays compact |
| HTML landing page with variables | Template render | Reusable template, dynamic data injection |
| Multi-file project scaffold | Data + driver | One data file drives many outputs |

## Real-World Origin

This skill was born from an actual blockage: generating a 14-page X profile analysis PDF where `write_file` silently truncated the ReportLab script every time. The fix was to serialize report content to JSON and run a compact driver. That pattern is now documented and reusable.

## License

MIT

## Contributing

Provider-specific limit data, additional strategies, and more examples welcome.
