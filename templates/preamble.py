"""
preamble.py

Include this snippet at the top of your `execute_code` calls to seamlessly 
wrap `sys.stdout` and redirect all printed output to a file in chunks,
bypassing tool truncation limits without changing your print() statements.
"""

import sys
import io

class ChunkedStdout:
    def __init__(self, path, chunk_size=12000):
        self.path = path
        self.chunk_size = chunk_size
        self.buffer = io.StringIO()
        
        # Clear the file initially
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("")

    def write(self, data):
        self.buffer.write(data)
        if self.buffer.tell() >= self.chunk_size:
            self.flush()

    def flush(self):
        content = self.buffer.getvalue()
        if content:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(content)
            # Reset buffer
            self.buffer.seek(0)
            self.buffer.truncate(0)

# Uncomment and set your path to use:
# sys.stdout = ChunkedStdout("/tmp/my_large_output.txt")
