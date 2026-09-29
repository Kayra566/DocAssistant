from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

ACTIVE_LLM = "llm.active"


class AppSetting(BaseModel):
    """Çalışma zamanında değiştirilebilen ayarlar (yeniden başlatma gerektirmez)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Süreçler arası önbellek geçersizleştirme için her yazmada artar.
    version: Mapped[int] = mapped_column(Integer, default=1)
