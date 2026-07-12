"""Code Tribunal — intent-conformance review for AI-generated code.

Ships three faces over one trial engine: the ``tribunal`` CLI, the
``tribunal-mcp`` MCP server, and the FastAPI backend behind the web demo.
"""

from .council import Analyzer

__version__ = "0.3.0"

__all__ = ["Analyzer", "__version__"]
