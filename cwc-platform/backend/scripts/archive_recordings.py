"""Move Zoom recordings into storage we own.

Zoom's download links stop working the moment a recording is deleted there, so
until this has run the media exists only in Zoom's account. Run this BEFORE
reducing Zoom seats or cancelling the storage add-on.

Usage — always start with a plan, and always test small:

    # 1. What's there? Writes nothing.
    python -m scripts.archive_recordings --plan

    # 2. One recording to a local folder, then go look at the file.
    python -m scripts.archive_recordings --limit 1 --dest ./recordings

    # 3. The rest. Safe to interrupt and re-run.
    python -m scripts.archive_recordings --dest ./recordings

    # Or straight to S3 (needs boto3 + AWS credentials):
    python -m scripts.archive_recordings --s3-bucket cwc-recordings

Needs a Zoom access token to download: --zoom-token, or ZOOM_ACCESS_TOKEN in
the environment. Without it Zoom returns a login page instead of the video.
"""
import argparse
import asyncio
import os
import sys

from app.database import async_session_maker
from app.services.recording_archive import (
    LocalStorage,
    S3Storage,
    archive_recordings,
    plan_archive,
)


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true",
                        help="list what would be archived; write nothing")
    parser.add_argument("--dry-run", action="store_true",
                        help="run the archive path but transfer nothing")
    parser.add_argument("--limit", type=int,
                        help="only process N recordings (use 1 for a first test)")
    parser.add_argument("--dest", default="./recordings",
                        help="local folder to archive into (default ./recordings)")
    parser.add_argument("--s3-bucket", help="archive to this S3 bucket instead")
    parser.add_argument("--s3-prefix", default="recordings/")
    parser.add_argument("--zoom-token", default=os.getenv("ZOOM_ACCESS_TOKEN"),
                        help="Zoom OAuth access token (or set ZOOM_ACCESS_TOKEN)")
    args = parser.parse_args()

    if args.s3_bucket:
        try:
            storage = S3Storage(args.s3_bucket, args.s3_prefix)
        except ImportError:
            print("boto3 is not installed. `pip install boto3` to archive to S3.")
            return 1
        where = f"s3://{args.s3_bucket}/{args.s3_prefix}"
    else:
        storage = LocalStorage(args.dest)
        where = args.dest

    async with async_session_maker() as db:
        if args.plan:
            plan = await plan_archive(db, storage)
            print(f"\n{plan['pending']} recording(s) to archive, "
                  f"{plan['already_archived']} already done.\n")
            for r in plan["recordings"][:50]:
                print(f"  {r['recorded_at'] or 'undated':<22} {r['title'] or '(untitled)'}")
            if plan["pending"] > 50:
                print(f"  ... and {plan['pending'] - 50} more")
            print(f"\nDestination: {where}")
            print("Nothing was written. Re-run without --plan to archive.\n")
            return 0

        if not args.zoom_token and not args.dry_run:
            print("\nNo Zoom token. Downloads will fail — Zoom returns a login")
            print("page rather than the video without one.")
            print("Pass --zoom-token or set ZOOM_ACCESS_TOKEN.\n")
            return 1

        print(f"\nArchiving to {where}"
              f"{' (DRY RUN — nothing will transfer)' if args.dry_run else ''}...\n")
        result = await archive_recordings(
            db, storage,
            access_token=args.zoom_token,
            dry_run=args.dry_run,
            limit=args.limit,
        )

        if args.dry_run:
            print(f"Would archive {result['would_archive']} recording(s).\n")
            return 0

        print(f"  archived: {result['archived']}")
        print(f"  skipped (already had bytes): {result['skipped']}")
        print(f"  failed: {result['failed']}")
        for err in result["errors"][:20]:
            print(f"    - {err}")
        if result["failed"]:
            print("\nFailures are safe to retry: re-run and only the missing ones")
            print("will be attempted. Do NOT delete anything from Zoom until this")
            print("reports zero failures.\n")
            return 1
        print("\nDone. Verify a few files open before deleting anything in Zoom.\n")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
