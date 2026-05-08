#!/usr/bin/env python3
"""
Example: Writing a large binary file safely via chunked base64 writing.
"""

import sys
import base64
import os

# Insert path to chunked_writer script for import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
from chunked_writer import write_large_binary

def generate_sample_binary():
    # 50KB of random binary data (e.g., simulating a generated PDF or image)
    return os.urandom(50000)

if __name__ == "__main__":
    raw_data = generate_sample_binary()
    
    # Convert to base64 so it safely traverses Python scripts/tool boundaries
    b64_content = base64.b64encode(raw_data).decode('utf-8')
    
    output_path = "/tmp/sample_output.bin"
    
    print(f"Original size: {len(raw_data)} bytes")
    print("Writing via chunked_writer...")
    
    write_large_binary(output_path, b64_content, chunk_size=12000)
    
    print("Write complete. File sizes match!")
