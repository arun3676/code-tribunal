from __future__ import annotations

import base64
import io
import os
from typing import Any

from openai import OpenAI
from PIL import Image

from .analyzer import MODEL_REGISTRY
from .prompts import build_multimodal_prompt

try:
    from google import genai as _google_genai
    from google.genai import types as _genai_types
except ImportError:  # pragma: no cover
    _google_genai = None
    _genai_types = None


class MultiModalAnalyzer:
    def __init__(self) -> None:
        self.vision_models = [item for item in MODEL_REGISTRY if item.vision]

    def get_available_models(self) -> list[dict[str, Any]]:
        return [item.to_dict(available=bool(os.getenv(item.env_var))) for item in self.vision_models]

    def analyze(self, image_bytes: bytes, prompt: str | None = None, model_id: str | None = None) -> dict[str, Any]:
        model_id = model_id or "gemini-2.5-flash"
        descriptor = next((item for item in self.vision_models if item.id == model_id), None)
        if descriptor is None:
            raise ValueError(f"Unsupported multimodal model: {model_id}")
        if not os.getenv(descriptor.env_var):
            raise ValueError(f"API key missing for {descriptor.display}")
        normalized_bytes, mime_type = self._normalize_image(image_bytes)
        final_prompt = build_multimodal_prompt(prompt)
        if descriptor.provider == "gemini":
            analysis = self._analyze_with_gemini(descriptor.id, normalized_bytes, mime_type, final_prompt)
        else:
            analysis = self._analyze_with_openai_vision(descriptor.id, descriptor.base_url or "", descriptor.env_var, normalized_bytes, mime_type, final_prompt)
        return {
            "analysis": analysis,
            "code_extracted": self._extract_code(analysis),
            "suggestions": self._extract_suggestions(analysis),
            "model": descriptor.id,
        }

    def _normalize_image(self, image_bytes: bytes) -> tuple[bytes, str]:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        max_size = 1600
        if max(image.size) > max_size:
            scale = max_size / max(image.size)
            image = image.resize((int(image.width * scale), int(image.height * scale)))
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=92)
        return output.getvalue(), "image/jpeg"

    def _analyze_with_gemini(self, model_id: str, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        if _google_genai is None:
            raise RuntimeError("google-genai is not installed")
        client = _google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=model_id,
            contents=[
                prompt,
                _genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
        )
        text = getattr(response, "text", None)
        if text:
            return text.strip()
        return ""

    def _analyze_with_openai_vision(self, model_id: str, base_url: str, env_var: str, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        client = OpenAI(api_key=os.getenv(env_var), base_url=base_url)
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            temperature=0.1,
        )
        return (response.choices[0].message.content or "").strip()

    def _extract_code(self, analysis: str) -> str:
        blocks: list[str] = []
        current: list[str] = []
        fenced = False
        for line in analysis.splitlines():
            if line.strip().startswith("```"):
                fenced = not fenced
                if not fenced and current:
                    blocks.append("\n".join(current).strip())
                    current = []
                continue
            if fenced:
                current.append(line)
        return "\n\n".join(blocks).strip()

    def _extract_suggestions(self, analysis: str) -> list[str]:
        suggestions: list[str] = []
        for line in analysis.splitlines():
            stripped = line.strip().lstrip("-*0123456789. ")
            lowered = stripped.lower()
            if any(keyword in lowered for keyword in ("suggest", "recommend", "consider", "improve", "risk")):
                suggestions.append(stripped)
        return suggestions[:6]
