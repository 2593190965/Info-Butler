import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("worker")


async def main():
    from backend.workers.worker_settings import WorkerSettings

    logger.info("Starting ARQ Worker...")

    from arq import create_worker

    worker = create_worker(WorkerSettings())
    await worker.run_async()

    logger.info("ARQ Worker stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested.")
        sys.exit(0)
