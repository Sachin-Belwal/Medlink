from dataclasses import dataclass
from typing import Optional
from os_simulator.cscan import estimate_latency_ms

@dataclass
class AllocationResult:
    strategy: str
    blocks: list[int]
    fragmentation_ratio: float
    predicted_latency_ms: float
    storage_preference: str

class AllocationError(RuntimeError):
    pass

def _free_blocks(conn) -> list[int]:
    rows = conn.execute(
        "SELECT block_id FROM DiskBlocks WHERE is_allocated = 0 ORDER BY block_id"
    ).fetchall()
    return [int(row["block_id"]) for row in rows]

def _find_contiguous_run(free: list[int], needed: int) -> Optional[list[int]]:
    if needed <= 0:
        return []
    run = []
    previous = None
    for block in free:
        if previous is None or block == previous + 1:
            run.append(block)
        else:
            run = [block]
        if len(run) >= needed:
            return run[:needed]
        previous = block
    return None

def _fragmentation_ratio(blocks: list[int]) -> float:
    if len(blocks) <= 1:
        return 0.0
    ordered = sorted(blocks)
    gaps = sum(1 for i in range(1, len(ordered)) if ordered[i] != ordered[i-1] + 1)
    return round(gaps / (len(ordered) - 1), 4)

def allocate_blocks(conn, file_id: int, needed: int, policy: str,
                    head: int = 50, storage_preference: str = "SPACE_EFFICIENT") -> AllocationResult:
    """Allocate blocks inside the caller's open SQL transaction."""
    if needed < 1:
        raise AllocationError("At least one block is required.")
    free = _free_blocks(conn)
    if len(free) < needed:
        raise AllocationError(f"Insufficient disk space: need {needed}, have {len(free)}.")

    policy = policy.upper()
    preference = storage_preference.upper()
    contiguous_first = policy == "CONTIGUOUS_FIRST" or preference == "CONTIGUOUS_FIRST"
    run = _find_contiguous_run(free, needed) if contiguous_first else None

    if run is not None:
        chosen = run
        strategy = "CONTIGUOUS"
    elif policy == "CONTIGUOUS_ONLY":
        raise AllocationError("No contiguous free run is large enough.")
    else:
        # SPACE_EFFICIENT and fallback after CONTIGUOUS_FIRST.
        chosen = free[:needed]
        strategy = "LINKED"

    # Update the virtual disk rows. All changes remain inside caller's transaction.
    for index, block in enumerate(chosen):
        next_block = chosen[index + 1] if index + 1 < len(chosen) else None
        conn.execute(
            """UPDATE DiskBlocks
               SET file_id = ?, next_block_id = ?, is_allocated = 1
               WHERE block_id = ? AND is_allocated = 0""",
            (file_id, next_block, block)
        )
        if conn.execute("SELECT changes()").fetchone()[0] != 1:
            raise AllocationError(f"Block {block} was not available for reservation.")

    # For linked allocation, selected free blocks can still happen to be adjacent.
    frag = _fragmentation_ratio(chosen)
    disk_size = conn.execute("SELECT COUNT(*) AS n FROM DiskBlocks").fetchone()["n"]
    safe_head = min(max(0, int(head)), int(disk_size) - 1)
    latency = estimate_latency_ms(chosen, safe_head, int(disk_size))
    return AllocationResult(
        strategy=strategy,
        blocks=chosen,
        fragmentation_ratio=frag,
        predicted_latency_ms=latency,
        storage_preference=preference
    )
