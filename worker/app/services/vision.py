import base64

import anthropic

from app.core.config import get_settings

_MEDIA_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}

TRANSCRIBE_PROMPT = (
    "Transcribe todo el contenido visible de esta imagen de un informe tecnico "
    "industrial o de laboratorio: texto, tablas (como texto delimitado), valores "
    "numericos con sus unidades, y una descripcion de cualquier grafica o curva "
    "(ejes, tendencia, valores aproximados de puntos clave). No interpretes ni "
    "resumas: transcribe fielmente lo que ves, en texto plano."
)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
    return _client


def transcribe_page(image_bytes: bytes, image_ext: str) -> str:
    media_type = _MEDIA_TYPES.get(image_ext.lower())
    if media_type is None:
        raise ValueError(f"unsupported image extension for vision: {image_ext}")

    response = _get_client().messages.create(
        model=get_settings().anthropic_vision_model,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.b64encode(image_bytes).decode("ascii"),
                        },
                    },
                    {"type": "text", "text": TRANSCRIBE_PROMPT},
                ],
            }
        ],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
