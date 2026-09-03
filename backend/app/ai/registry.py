"""Model kayıt defteri: `MODELS_DIR` içindeki dosyaları ve Ollama modellerini keşfeder."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

GGUF_SUFFIX = ".gguf"


@dataclass(frozen=True)
class ModelInfo:
    """Arayüzde listelenen tek bir model."""

    id: str
    name: str
    # ollama: sunucuda hazır | file: klasörde, henüz içe aktarılmamış | builtin: sahte
    source: str
    ready: bool
    size_bytes: int = 0
    detail: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


BUILTIN = ModelInfo(
    id="builtin:fake",
    name="Yerleşik (demo yanıtlar)",
    source="builtin",
    ready=True,
    detail="Model gerektirmez; geliştirme ve testler için deterministik yanıt üretir.",
)


def models_dir() -> Path:
    path = Path(settings.MODELS_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _file_models(imported: set[str]) -> list[ModelInfo]:
    """Klasöre bırakılmış .gguf dosyaları."""
    found: list[ModelInfo] = []
    for path in sorted(models_dir().glob(f"*{GGUF_SUFFIX}")):
        tag = path.stem.lower()
        ready = any(name.split(":")[0] == tag for name in imported)
        found.append(
            ModelInfo(
                id=f"file:{path.name}",
                name=path.stem,
                source="file",
                ready=ready,
                size_bytes=path.stat().st_size,
                detail=(
                    "Kullanıma hazır."
                    if ready
                    else "Klasörde bulundu; kullanmak için içe aktarın."
                ),
            )
        )
    return found


async def _ollama_models() -> list[ModelInfo]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        logger.info("Ollama erişilemedi: %s", exc)
        return []

    return [
        ModelInfo(
            id=f"ollama:{item['name']}",
            name=item["name"],
            source="ollama",
            ready=True,
            size_bytes=int(item.get("size", 0)),
            detail="Ollama sunucusunda hazır.",
        )
        for item in payload.get("models", [])
        if item.get("name")
    ]


async def discover() -> list[ModelInfo]:
    """Kullanılabilir tüm modeller; her zaman en az yerleşik sağlayıcı döner."""
    ollama = await _ollama_models()
    imported = {model.name for model in ollama}
    return [BUILTIN, *ollama, *_file_models(imported)]


async def ollama_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            return (
                await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            ).is_success
    except Exception:
        return False


async def import_gguf(filename: str) -> str:
    """Klasördeki bir .gguf dosyasını Ollama'ya kaydeder ve model adını döndürür."""
    from app.core.exceptions import ValidationError

    safe_name = Path(filename).name
    path = models_dir() / safe_name
    if not path.is_file() or path.suffix.lower() != GGUF_SUFFIX:
        raise ValidationError(f"{safe_name} bulunamadı veya .gguf değil.")

    model_name = path.stem.lower()
    # Ollama konteyneri aynı klasörü kendi mount yolundan görür.
    container_path = f"{settings.MODELS_MOUNT_PATH.rstrip('/')}/{safe_name}"

    async with httpx.AsyncClient(timeout=settings.MODEL_IMPORT_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/create",
            json={"name": model_name, "modelfile": f"FROM {container_path}"},
        )
        if not response.is_success:
            raise ValidationError(
                f"Ollama modeli içe aktaramadı: {response.text[:200]}"
            )

    return model_name
