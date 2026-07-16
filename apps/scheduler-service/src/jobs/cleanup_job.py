import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.settings import settings
from packages.shared.storage.minio import MinioStorageClient
from packages.shared.vector.qdrant import QdrantVectorStore

logger = logging.getLogger("scheduler_service.jobs.cleanup")

# Optimize DB engine for cleanup operations
_engine = None
_session_maker = None

def get_session_maker():
    global _engine, _session_maker
    if _session_maker is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True
        )
        _session_maker = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
    return _session_maker


async def execute_cleanup_job() -> None:
    """Queries, deletes, and garbage-collects expired data across all tiers (Postgres, MinIO, Qdrant)."""
    logger.info("Database retention cleanup run started...")
    
    retention_cutoff = datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS)
    logger.info(f"Retention threshold cutoff: {retention_cutoff.isoformat()}")

    # 1. Initialize Clients
    qdrant_store = QdrantVectorStore()
    minio_client = MinioStorageClient(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False
    )

    async_session_local = get_session_maker()
    async with async_session_local() as session:
        try:
            # ============================================================
            # A. FETCH RETIRED DATA FOR FILE & VECTOR CLEANUP
            # ============================================================
            
            # 1. Get tracking events crop paths
            tracking_res = await session.execute(
                text("SELECT id, person_id, crop_path FROM tracking_events WHERE timestamp < :cutoff"),
                {"cutoff": retention_cutoff}
            )
            tracking_rows = tracking_res.all()
            tracking_ids = [row[0] for row in tracking_rows]
            tracking_pids = [row[1] for row in tracking_rows if row[1] is not None]
            tracking_crops = [row[2] for row in tracking_rows if row[2]]
            
            # 2. Get fire events crop paths
            fire_res = await session.execute(
                text("SELECT id, crop_path FROM fire_events WHERE timestamp < :cutoff"),
                {"cutoff": retention_cutoff}
            )
            fire_rows = fire_res.all()
            fire_ids = [row[0] for row in fire_rows]
            fire_crops = [row[1] for row in fire_rows if row[1]]

            # 3. Get expired persons (no updates since cutoff)
            person_res = await session.execute(
                text("SELECT id FROM persons WHERE last_seen < :cutoff"),
                {"cutoff": retention_cutoff}
            )
            expired_person_ids = [row[0] for row in person_res.all()]

            logger.info(
                f"Found {len(tracking_ids)} expired tracking events, "
                f"{len(fire_ids)} expired fire events, "
                f"and {len(expired_person_ids)} expired persons."
            )

            # ============================================================
            # B. EXECUTE HARD DELETE ON VECTOR STORE (Qdrant)
            # ============================================================
            if expired_person_ids:
                logger.info(f"Removing {len(expired_person_ids)} person vector embeddings from Qdrant...")
                try:
                    await qdrant_store.delete_embeddings(expired_person_ids)
                except Exception as e:
                    logger.error(f"Failed to clean up vectors in Qdrant: {e}")

            # ============================================================
            # C. EXECUTE HARD DELETE ON OBJECT STORAGE (MinIO)
            # ============================================================
            all_crops_to_delete = tracking_crops + fire_crops
            if all_crops_to_delete:
                logger.info(f"Removing {len(all_crops_to_delete)} crop images from MinIO...")
                for crop_path in all_crops_to_delete:
                    try:
                        parts = crop_path.split("/", 1)
                        if len(parts) == 2:
                            bucket, obj_name = parts[0], parts[1]
                        else:
                            bucket, obj_name = settings.MINIO_BUCKET_CROPS, parts[0]
                            
                        minio_client.delete_object(bucket, obj_name)
                    except Exception as e:
                        logger.error(f"Failed to delete crop object '{crop_path}': {e}")

            # ============================================================
            # D. EXECUTE DATABASE DELETES (PostgreSQL)
            # ============================================================
            # Delete tracking events
            if tracking_ids:
                await session.execute(
                    text("DELETE FROM tracking_events WHERE id = ANY(:ids)"),
                    {"ids": tracking_ids}
                )
            
            # Delete fire events
            if fire_ids:
                await session.execute(
                    text("DELETE FROM fire_events WHERE id = ANY(:ids)"),
                    {"ids": fire_ids}
                )

            # Delete associated alerts
            alert_del = await session.execute(
                text("DELETE FROM alerts WHERE timestamp < :cutoff"),
                {"cutoff": retention_cutoff}
            )
            logger.info(f"Deleted {alert_del.rowcount} expired alerts from alerts table.")

            # Delete persons
            if expired_person_ids:
                await session.execute(
                    text("DELETE FROM persons WHERE id = ANY(:ids)"),
                    {"ids": expired_person_ids}
                )

            # Commit the transaction
            await session.commit()
            logger.info("Successfully committed all Postgres database retention deletions.")

        except Exception as e:
            logger.error(f"Transaction failed during database cleanup run: {e}", exc_info=True)
            await session.rollback()
            raise e
        finally:
            await session.close()
            
    logger.info("Retention cleanup completed successfully.")
