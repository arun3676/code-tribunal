"""Code Council — the multi-model analysis engine behind the `/council` editor.

This is the original product surface: paste code, stream several model opinions
over it in parallel, and compare where they agree or miss things. It is kept
separate from `code_council.tribunal` (the intent-conformance court), which is
the flagship engine and shares none of this code — only the FastAPI server
mounts both.
"""

from .analyzer import Analyzer
from .fixes import FixSuggestionGenerator
from .language import LanguageDetector
from .multimodal import MultiModalAnalyzer

__all__ = [
    "Analyzer",
    "FixSuggestionGenerator",
    "LanguageDetector",
    "MultiModalAnalyzer",
]
