"""History and settings persistence services."""

from __future__ import annotations

from sqlalchemy import delete, select

from backend.database.session import async_session_factory
from backend.models.schemas import AppSettingsRecord, DownloadRecord, HistoryItem, SettingsSchema


class HistoryService:
    """CRUD operations for download history."""

    async def list_history(
        self, query: str = "", favorite_only: bool = False
    ) -> list[HistoryItem]:
        async with async_session_factory() as session:
            stmt = select(DownloadRecord).order_by(DownloadRecord.created_at.desc())
            if favorite_only:
                stmt = stmt.where(DownloadRecord.is_favorite.is_(True))
            result = await session.execute(stmt)
            records = result.scalars().all()

            if query:
                q = query.lower()
                records = [
                    r
                    for r in records
                    if q in r.title.lower() or q in r.url.lower()
                ]

            return [HistoryItem.model_validate(r) for r in records]

    async def delete(self, record_id: int) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(
                delete(DownloadRecord).where(DownloadRecord.id == record_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def toggle_favorite(self, record_id: int) -> HistoryItem | None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(DownloadRecord).where(DownloadRecord.id == record_id)
            )
            record = result.scalar_one_or_none()
            if not record:
                return None
            record.is_favorite = not record.is_favorite
            await session.commit()
            await session.refresh(record)
            return HistoryItem.model_validate(record)


class SettingsService:
    """Application settings persistence."""

    async def get_settings(self) -> SettingsSchema:
        async with async_session_factory() as session:
            result = await session.execute(
                select(AppSettingsRecord).where(AppSettingsRecord.id == 1)
            )
            record = result.scalar_one_or_none()
            if not record:
                record = AppSettingsRecord(id=1)
                session.add(record)
                await session.commit()
                await session.refresh(record)
            return SettingsSchema.model_validate(record)

    async def update_settings(self, settings: SettingsSchema) -> SettingsSchema:
        async with async_session_factory() as session:
            result = await session.execute(
                select(AppSettingsRecord).where(AppSettingsRecord.id == 1)
            )
            record = result.scalar_one_or_none()
            if not record:
                record = AppSettingsRecord(id=1)
                session.add(record)

            for key, value in settings.model_dump().items():
                setattr(record, key, value)

            await session.commit()
            await session.refresh(record)
            return SettingsSchema.model_validate(record)


history_service = HistoryService()
settings_service = SettingsService()
