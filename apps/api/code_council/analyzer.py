from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from .fixes import FixSuggestionGenerator
from .language import LanguageDetector
from .models import CodeAnalysisResult, ModelDescriptor
from .prompts import build_analysis_prompt
from .utils import parse_llm_response, timer_decorator

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None


load_dotenv()


MODEL_REGISTRY: tuple[ModelDescriptor, ...] = (
    ModelDescriptor(
        id="gemini-2.5-flash",
        provider="gemini",
        display="Gemini",
        color="#4285F4",
        env_var="GEMINI_API_KEY",
        vision=True,
    ),
    ModelDescriptor(
        id="deepseek-chat",
        provider="deepseek",
        display="DeepSeek",
        color="#00FF66",
        env_var="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
    ),
    ModelDescriptor(
        id="mercury-coder-small",
        provider="mercury",
        display="Mercury",
        color="#FF8A65",
        env_var="MERCURY_API_KEY",
        base_url="https://api.inceptionlabs.ai/v1",
    ),
    ModelDescriptor(
        id="moonshot-v1-8k",
        provider="kimi",
        display="Kimi",
        color="#9C27B0",
        env_var="Kimi_API_KEY",
        base_url="https://api.moonshot.ai/v1",
        vision=True,
    ),
)


class Analyzer:
    def __init__(self) -> None:
        self.language_detector = LanguageDetector()
        self.fix_generator = FixSuggestionGenerator()

    def get_model_registry(self) -> list[ModelDescriptor]:
        return list(MODEL_REGISTRY)

    def get_available_models(self) -> list[dict[str, Any]]:
        return [descriptor.to_dict(available=bool(os.getenv(descriptor.env_var))) for descriptor in MODEL_REGISTRY]

    def is_model_available(self, model_id: str) -> bool:
        descriptor = self.get_model_descriptor(model_id)
        return bool(os.getenv(descriptor.env_var))

    def get_model_descriptor(self, model_id: str) -> ModelDescriptor:
        for descriptor in MODEL_REGISTRY:
            if descriptor.id == model_id:
                return descriptor
        raise ValueError(f"Unsupported model: {model_id}")

    def resolve_language(self, code: str, language: str | None = None, file_path: str | None = None) -> str:
        if language and language != "auto":
            return language
        return self.language_detector.detect_language(code, file_path=file_path).name

    def prepare_analysis(self, code: str, model: str, language: str | None = None, mode: str = "quick") -> tuple[ModelDescriptor, str, str]:
        if not code.strip():
            raise ValueError("Code input is empty")
        descriptor = self.get_model_descriptor(model)
        if not os.getenv(descriptor.env_var):
            raise ValueError(f"API key missing for {descriptor.display}")
        detected_language = self.resolve_language(code, language=language)
        prompt = build_analysis_prompt(code=code, language=detected_language, mode=mode)
        return descriptor, detected_language, prompt

    def generate_analysis_text(self, code: str, model: str, language: str | None = None, mode: str = "quick") -> tuple[str, str]:
        descriptor, detected_language, prompt = self.prepare_analysis(code, model, language=language, mode=mode)
        return detected_language, self._generate_text(descriptor, prompt)

    @timer_decorator
    def analyze_code(self, code: str, model: str, language: str | None = None, mode: str = "quick") -> CodeAnalysisResult:
        descriptor, detected_language, _ = self.prepare_analysis(code, model, language=language, mode=mode)
        started_at = time.perf_counter()
        _, raw_response = self.generate_analysis_text(code, model, language=language, mode=mode)
        parsed = parse_llm_response(raw_response)
        result = CodeAnalysisResult(
            code_quality_score=float(parsed.get("code_quality_score", 70)),
            potential_bugs=list(parsed.get("potential_bugs", [])),
            improvement_suggestions=list(parsed.get("improvement_suggestions", [])),
            documentation=str(parsed.get("documentation", "")).strip(),
            model_name=descriptor.id,
            execution_time=time.perf_counter() - started_at,
            raw_response=raw_response,
        )
        if mode == "thorough":
            issues = [
                {
                    "type": "bug",
                    "description": item,
                    "line_number": 0,
                    "severity": "medium",
                }
                for item in result.potential_bugs
            ] + [
                {
                    "type": "improvement",
                    "description": item,
                    "line_number": 0,
                    "severity": "low",
                }
                for item in result.improvement_suggestions
            ]
            result.fix_suggestions = self.fix_generator.generate_fix_suggestions(code, issues, detected_language)
        return result

    def _generate_text(self, descriptor: ModelDescriptor, prompt: str) -> str:
        if descriptor.provider == "gemini":
            return self._generate_with_gemini(descriptor, prompt)
        client = OpenAI(api_key=os.getenv(descriptor.env_var), base_url=descriptor.base_url)
        response = client.chat.completions.create(
            model=descriptor.id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return (response.choices[0].message.content or "").strip()

    def _generate_with_gemini(self, descriptor: ModelDescriptor, prompt: str) -> str:
        if genai is None:
            raise RuntimeError("google-generativeai is not installed")
        api_key = os.getenv(descriptor.env_var)
        if not api_key:
            raise ValueError(f"API key missing for {descriptor.display}")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(descriptor.id)
        response = model.generate_content(prompt)
        text = getattr(response, "text", None)
        if text:
            return text.strip()
        candidates = getattr(response, "candidates", []) or []
        parts: list[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                if getattr(part, "text", None):
                    parts.append(part.text)
        return "\n".join(parts).strip()
