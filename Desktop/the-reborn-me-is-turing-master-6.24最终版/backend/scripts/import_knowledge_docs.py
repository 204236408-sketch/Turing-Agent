"""Import all knowledge_docs markdown files into ChromaDB knowledge_base_408 collection.

Usage:
    python scripts/import_knowledge_docs.py                # rebuild + import (default)
    python scripts/import_knowledge_docs.py --dry-run       # preview only, no write
    python scripts/import_knowledge_docs.py --strategy sliding_window  # use sliding window strategy
    python scripts/import_knowledge_docs.py --target-chars 600 --overlap-chars 200  # custom params
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import PROJECT_DIR
from services.chunk_optimizer import (
    ChunkConfig,
    batch_chunk,
    chunk_statistics,
)
from services.chroma_service import (
    chroma_status,
    get_or_create_collection,
    delete_collection,
    upsert_document,
)
from services.vector_embedding_service import embedding_status


DOCS_DIR = PROJECT_DIR / "knowledge_docs"
COLLECTION = "knowledge_base_408"


def parse_args() -> dict:
    args = {
        "dry_run": False,
        "strategy": "hierarchical",
        "target_chars": 800,
        "overlap_chars": 150,
        "max_chars": 2000,
    }
    argv = [a.lower() for a in sys.argv]
    if "--dry-run" in argv:
        args["dry_run"] = True

    for arg in sys.argv:
        if arg.startswith("--strategy="):
            args["strategy"] = arg.split("=", 1)[1]
        elif arg.startswith("--target-chars="):
            args["target_chars"] = int(arg.split("=", 1)[1])
        elif arg.startswith("--overlap-chars="):
            args["overlap_chars"] = int(arg.split("=", 1)[1])
        elif arg.startswith("--max-chars="):
            args["max_chars"] = int(arg.split("=", 1)[1])

    return args


def rebuild_and_import(cli_args: dict) -> dict:
    config = ChunkConfig(
        strategy=cli_args["strategy"],
        target_chars=cli_args["target_chars"],
        overlap_chars=cli_args["overlap_chars"],
        max_chars=cli_args["max_chars"],
    )

    result = {
        "config": {
            "strategy": config.strategy,
            "target_chars": config.target_chars,
            "overlap_chars": config.overlap_chars,
            "max_chars": config.max_chars,
        },
        "docs_found": 0,
        "chunks_total": 0,
        "imported": 0,
        "failed": 0,
        "errors": [],
        "statistics": {},
    }

    md_files = sorted(DOCS_DIR.rglob("*.md"))
    result["docs_found"] = len(md_files)
    if not md_files:
        return {**result, "error": "no md files found in knowledge_docs/"}

    all_chunks = batch_chunk(DOCS_DIR, config)
    result["chunks_total"] = len(all_chunks)
    result["statistics"] = chunk_statistics(all_chunks)

    if cli_args["dry_run"]:
        return result

    status = chroma_status()
    if not status["enabled"]:
        return {**result, "error": f"chromadb not enabled: {status.get('error')}"}

    emb_status = embedding_status()
    if not emb_status["available"]:
        return {**result, "error": f"embedding not available: {emb_status.get('error')}"}

    print(f"Rebuilding collection '{COLLECTION}' ...")
    existing = get_or_create_collection(COLLECTION)
    if existing is not None:
        try:
            count_before = len(existing.get()["ids"])
            print(f"  Existing docs: {count_before}")
        except Exception:
            pass
        delete_collection(COLLECTION)
        time.sleep(0.5)

    coll = get_or_create_collection(COLLECTION)
    if coll is None:
        return {**result, "error": "failed to create collection"}

    for i, chunk in enumerate(all_chunks):
        upsert_result = upsert_document(
            COLLECTION,
            chunk.document_id,
            chunk.text,
            chunk.metadata,
        )
        if upsert_result.get("stored"):
            result["imported"] += 1
        else:
            result["failed"] += 1
            err = upsert_result.get("error", "unknown")
            result["errors"].append(f"{chunk.document_id}: {err}")
            if len(result["errors"]) > 10:
                result["errors"].append("... (truncated)")
                break

        if (i + 1) % 50 == 0:
            print(f"  Imported {i + 1}/{len(all_chunks)} ...")

    try:
        final = coll.get()
        result["final_count"] = len(final.get("ids", []))
    except Exception:
        pass

    return result


def print_result(r: dict) -> None:
    print(f"\n{'='*55}")
    print(f"Import Results")
    print(f"{'='*55}")
    cfg = r.get("config", {})
    print(f"  Strategy      : {cfg.get('strategy', 'N/A')}")
    print(f"  Target chars  : {cfg.get('target_chars', 'N/A')}")
    print(f"  Overlap chars : {cfg.get('overlap_chars', 'N/A')}")
    print(f"  Max chars     : {cfg.get('max_chars', 'N/A')}")
    print(f"  Docs found    : {r['docs_found']}")
    print(f"  Chunks total  : {r['chunks_total']}")
    print(f"  Imported      : {r['imported']}")
    print(f"  Failed        : {r['failed']}")
    if "final_count" in r:
        print(f"  Final in DB   : {r['final_count']}")
    stats = r.get("statistics", {})
    if stats:
        print(f"  Avg chars     : {stats.get('avg_chars', '-')}")
        print(f"  Min/Max chars : {stats.get('min_chars', '-')}/{stats.get('max_chars', '-')}")
        if stats.get("by_subject"):
            print(f"  By subject:")
            for subj, count in sorted(stats["by_subject"].items()):
                print(f"    {subj}: {count} chunks")
        if stats.get("by_strategy"):
            print(f"  By strategy:")
            for s, count in sorted(stats["by_strategy"].items()):
                print(f"    {s}: {count} chunks")
    if r.get("errors"):
        print(f"  Errors ({len(r['errors'])}):")
        for e in r["errors"][:5]:
            print(f"    - {e}")
    if r.get("error"):
        print(f"  FATAL: {r['error']}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    cli_args = parse_args()

    if cli_args["dry_run"]:
        print("[DRY RUN] Preview only, no writes\n")
    else:
        print(f"Rebuilding '{COLLECTION}' from {DOCS_DIR} ...")

    result = rebuild_and_import(cli_args)
    print_result(result)

    if cli_args["dry_run"]:
        print("Run without --dry-run to execute the import.")
