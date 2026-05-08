---
name: chunked-code-generation
description: Reliably generate large scripts, files, and artifacts when Hermes tools silently truncate content. Three strategies: chunked writes, data-separation with driver scripts, and lightweight template rendering. Essential for Cloudflare Workers AI / Kimi K-2.6 users where write_file truncates at ~15K chars.
version: 2.0.0
author: Vaibhav Sharma + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-generation, chunked-write, large-files, cloudflare, kimi-k2, workaround, tooling]
    related_skills: [plan, subagent-driven-development]
---

# Chunked Code Generation

Generate large files reliably when Hermes tools impose silent content length limits.

## The Problem

Hermes file tools (`write_file`, `patch` with large replacements) and code execution have implicit character limits. When exceeded, content is **silently truncated** mid-file, leading to:

- IndentationError / SyntaxError in generated scripts
- Missing closing tags in HTML/XML
- Incomplete data structures in JSON
- Wasted time debugging corrupted output

This is most acute on **Cloudflare Workers AI with Kimi K-2.6** where `write_file` truncates around 15,000 characters.

## The Solution: Five Strategies

### Strategy 1: Chunked File Write (Raw Text)

Use when you need to write a large text file (HTML, markdown, YAML, SQL dump) and the content fits in memory.

```python
# In execute_code:
import sys
sys.path.insert(0, "/home/yash/.hermes/skills/software-development/chunked-code-generation/scripts")
from chunked_writer import write_large_file

content = "..."  # Your large string, e.g. 50K chars of HTML
write_large_file("/path/to/output.html", content, chunk_size=12000)
```

This writes the file in 12K-character chunks using Python file I/O. No tool truncation.

### Strategy 2: Chunked File Write (Binary)

Use when you need to write a large binary file (PDF, images, executable) from memory (like base64 chunks).

```python
from chunked_writer import write_large_binary
b64_content = "..." # Your large base64 string
write_large_binary("/path/to/output.pdf", b64_content, chunk_size=12000)
```

### Strategy 3: Safe Find-And-Replace

The `patch` tool also fails on replacements larger than 15K characters. Use this strategy to perform targeted find-and-replace using Python I/O instead.

```python
from chunked_writer import replace_large_block
replace_large_block("app.py", "old_large_string", "new_large_string")
```

### Strategy 4: Data Separation + Driver Script (Recommended for Complex Generation)

Use when generating structured artifacts (PDFs, reports, dashboards) where static content is large but the generation logic is compact.

**Step A:** Save your static data as JSON via a small `execute_code` call.

```python
from hermes_tools import read_file  # or construct in Python
import json

data = {
    "title": "X Profile Analysis",
    "sections": [...],
    "stats": {"followers": 215, "posts": 245}
}
with open("/tmp/my_data.json", "w") as f:
    json.dump(data, f)
print("Data saved")
```

**Step B:** Write a compact driver script (<8K chars) that reads the JSON and generates the artifact.

```python
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph

with open("/tmp/my_data.json") as f:
    data = json.load(f)

doc = SimpleDocTemplate("output.pdf")
story = [Paragraph(data["title"])]
# ... build from data ...
doc.build(story)
```

**Step C:** Execute the driver in one call.

```python
# execute_code reads /tmp/my_data.json and runs the generation
```

**Why this works:** The data JSON can be arbitrarily large. The driver script stays under the tool limit. The generation happens inside Python, not across Hermes tool boundaries.

### Strategy 5: Template Rendering

Use when the output is mostly static with variable substitution (HTML landing pages, email templates, configuration files).

```python
from chunked_writer import render_template

data = {"company": "Kubar Labs", "tagline": "Credit rails for 64M MSMEs"}
render_template("template.html", data, "output.html",
                placeholder_fmt="{{{{{key}}}}}")
```

Template syntax uses triple braces to avoid collision with JSON/Python:

```html
<h1>{{{company}}}</h1>
<p>{{{tagline}}}</p>
```

## Anti-Patterns (What NOT to Do)

| Anti-Pattern | Why It Fails |
|---|---|
| Write a 20K-char script via `write_file` | Truncated mid-file -> SyntaxError |
| Chain multiple `execute_code` calls for one script | Variables from call N don't exist in call N+1 |
| Use `patch` with a 15K-char replacement string | Same truncation as `write_file` |
| Rely on print debugging across tool boundaries | Output truncated at ~50KB |

## Diagnostics

### Detect Your Tool's Write Limit

```bash
python3 ~/.hermes/skills/software-development/chunked-code-generation/scripts/chunked_writer.py detect
```

Tests incremental sizes and reports where truncation begins.

### Check if a Generated File is Truncated

```python
# In execute_code:
import os
path = "/path/to/output.py"
expected_chars = 25000
actual = os.path.getsize(path)
print(f"Expected ~{expected_chars}, got {actual}")
if actual < expected_chars * 0.95:
    print("WARNING: File may be truncated!")
```

## When to Use Which Strategy

| Scenario | Strategy | Example |
|---|---|---|
| Large raw text file (>15K chars) | Strategy 1: Chunked write | SQL dump, markdown doc |
| Binary payload (PDF, image via base64) | Strategy 2: Chunked binary | Auto-generated PDF payload |
| Large string find-and-replace | Strategy 3: Safe Replace | Replacing big JSON objects in app.py |
| PDF / report generation with data tables | Strategy 4: Data + driver | Profile analysis report |
| HTML landing page with variable content | Strategy 5: Template | Marketing page, email |
| Multi-file project scaffold | Strategy 4: Data + driver | React/Vue component tree |

## Real-World Example: X Profile Analysis Report

See `examples/generate_pdf_report.py` for the complete working example from which this skill was born. It generates a 14-page PDF report by:

1. Parsing 245 posts into stats (engagement, themes, dates)
2. Saving report content structure as JSON
3. Running a compact ReportLab driver that reads both and builds the PDF

## Files in This Skill

```
chunked-code-generation/
  SKILL.md                          # This file
  scripts/
    chunked_writer.py               # Core helper library
  examples/
    generate_pdf_report.py          # ReportLab PDF example
    generate_static_site.py         # HTML template example
  templates/
    report_template.py              # Starter template for Strategy 2
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| IndentationError on generated script | `write_file` truncated mid-file | Use Strategy 2 or 1 |
| NameError for variable defined earlier | Chained `execute_code` lost state | Merge into single call with `serialize_data` |
| PDF/PNG missing pages or sections | ReportLab story too large for one `build()` | Nothing, `build()` handles it. Check data JSON for truncation |
| `detect` shows truncation at 15K | Provider tool limit (Cloudflare/Kimi) | Use `chunk_size=12000` |
| `detect` shows truncation at 100K+ | You are fine; write directly | No workaround needed |

## Notes

- The 15K limit observed on Cloudflare Workers AI / Kimi K-2.6 is a **tool-level limit**, not a model context window limit. The model itself has a 262K context window, but the `write_file` tool truncates before that.
- Always verify output file size when generating artifacts >15K characters.
- This skill is a **workaround**. The proper fix is for Hermes to natively support chunked file uploads or streaming writes.

## Open-Source

This skill is maintained at: https://github.com/fenestbuc/hermes-chunked-code-generation

Contributions welcome: additional strategies, provider-specific limit data, more examples.
