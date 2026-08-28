"""Verify ECO-1702 media lifecycle constraints in Supabase test with rollback."""

import asyncio
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def rejected(connection: AsyncConnection, statement: str, values: dict[str, object]) -> bool:
    savepoint = await connection.begin_nested()
    try:
        await connection.execute(text(statement), values)
    except SQLAlchemyError as exc:
        await savepoint.rollback()
        if not isinstance(exc, DBAPIError):
            return False
        original = exc.orig
        return (
            getattr(original, "sqlstate", None) == "23514"
            and getattr(getattr(original, "diag", None), "constraint_name", "")
            in {
                "media_assets_checksum_sha256_check",
                "media_assets_dimensions_check",
                "media_assets_license_code_check",
                "media_assets_processing_result_check",
                "media_assets_quarantine_check",
                "media_assets_storage_mode_check",
            }
        )
    await savepoint.rollback()
    return False


async def verify_constraints(connection: AsyncConnection) -> dict[str, bool]:
    owner_id = uuid.uuid4()
    base = {
        "owner_id": owner_id,
        "storage_key": f"routes/{owner_id}/hero.webp",
        "checksum": "a" * 64,
    }
    ready_statement = (
        "insert into app_private.media_assets "
        "(owner_type, owner_id, storage_key, mime_type, alt_text, credit, license_code, "
        "processing_status, checksum_sha256, width_px, height_px, processed_at, derivatives) "
        "values ('route', :owner_id, :storage_key, 'image/webp', 'Vista da rota', "
        "'SEMTUR', 'SEMTUR_INSTITUTIONAL', 'ready', :checksum, 1200, 800, now(), "
        "'{\"thumb\": {\"storage_key\": \"thumb.webp\", \"checksum_sha256\": "
        "\"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\"}, "
        "\"card\": {\"storage_key\": \"card.webp\", \"checksum_sha256\": "
        "\"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc\"}, "
        "\"hero\": {\"storage_key\": \"hero.webp\", \"checksum_sha256\": "
        "\"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd\"}}'::jsonb) "
        "returning id"
    )
    media_id = (await connection.execute(text(ready_statement), base)).scalar_one()

    invalid_ready = await rejected(
        connection,
        ready_statement.replace("'SEMTUR_INSTITUTIONAL'", "NULL"),
        {**base, "storage_key": f"routes/{owner_id}/invalid-license.webp"},
    )
    invalid_checksum = await rejected(
        connection,
        ready_statement,
        {
            **base,
            "storage_key": f"routes/{owner_id}/invalid-checksum.webp",
            "checksum": "invalid",
        },
    )
    invalid_quarantine = await rejected(
        connection,
        "insert into app_private.media_assets "
        "(owner_type, owner_id, storage_key, mime_type, deleted_at) "
        "values ('route', :owner_id, :storage_key, 'image/webp', now())",
        {**base, "storage_key": f"routes/{owner_id}/invalid-quarantine.webp"},
    )
    partial_dimensions = await rejected(
        connection,
        "insert into app_private.media_assets "
        "(owner_type, owner_id, storage_key, mime_type, width_px) "
        "values ('route', :owner_id, :storage_key, 'image/webp', 100)",
        {**base, "storage_key": f"routes/{owner_id}/partial-dimensions.webp"},
    )
    ready_without_alt = await rejected(
        connection,
        ready_statement.replace("'Vista da rota'", "NULL"),
        {**base, "storage_key": f"routes/{owner_id}/without-alt.webp"},
    )
    ready_without_derivatives = await rejected(
        connection,
        ready_statement.replace(
            "'{\"thumb\": {\"storage_key\": \"thumb.webp\", \"checksum_sha256\": "
            "\"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\"}, "
            "\"card\": {\"storage_key\": \"card.webp\", \"checksum_sha256\": "
            "\"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc\"}, "
            "\"hero\": {\"storage_key\": \"hero.webp\", \"checksum_sha256\": "
            "\"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd\"}}'::jsonb",
            "'{}'::jsonb",
        ),
        {**base, "storage_key": f"routes/{owner_id}/without-derivatives.webp"},
    )
    ready_with_empty_derivatives = await rejected(
        connection,
        ready_statement.replace(
            "'{\"thumb\": {\"storage_key\": \"thumb.webp\", \"checksum_sha256\": "
            "\"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\"}, "
            "\"card\": {\"storage_key\": \"card.webp\", \"checksum_sha256\": "
            "\"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc\"}, "
            "\"hero\": {\"storage_key\": \"hero.webp\", \"checksum_sha256\": "
            "\"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd\"}}'::jsonb",
            "'{\"thumb\": {}, \"card\": {}, \"hero\": {}}'::jsonb",
        ),
        {**base, "storage_key": f"routes/{owner_id}/empty-derivatives.webp"},
    )
    legacy_columns = (
        await connection.execute(
            text(
                "select count(*) from information_schema.columns "
                "where table_schema = 'app_private' and table_name = 'media_assets' "
                "and column_name = any(array['media_kind', 'external_photo_reference', "
                "'external_attributions', 'external_cache_expires_at'])"
            )
        )
    ).scalar_one()
    google_license_rejected = await rejected(
        connection,
        ready_statement.replace("'SEMTUR_INSTITUTIONAL'", "'GOOGLE_PLACES_PROXY'"),
        {**base, "storage_key": f"routes/{owner_id}/google-license.webp"},
    )
    return {
        "ready accepted": media_id is not None,
        "ready without license rejected": invalid_ready,
        "invalid checksum rejected": invalid_checksum,
        "delete outside quarantine rejected": invalid_quarantine,
        "partial dimensions rejected": partial_dimensions,
        "ready without alt rejected": ready_without_alt,
        "ready without derivatives rejected": ready_without_derivatives,
        "ready with empty derivative objects rejected": ready_with_empty_derivatives,
        "legacy Google proxy columns removed": legacy_columns == 0,
        "Google proxy license rejected": google_license_rejected,
    }


async def verify() -> int:
    load_dotenv(BACKEND_DIR / ".env.test", override=True)
    engine = create_async_engine(Settings().DATABASE_URL.get_secret_value())
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                results = await verify_constraints(connection)
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()

    failures = [name for name, passed in results.items() if not passed]
    if failures:
        print("MEDIA_LIFECYCLE=ERROR")
        for failure in failures:
            print(f"- categoria: {failure.upper().replace(' ', '_')}")
        return 1
    print("MEDIA_LIFECYCLE=OK")
    for name in results:
        print(f"- {name}")
    print("- todas as escritas revertidas")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
