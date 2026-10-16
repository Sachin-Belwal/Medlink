from typing import Iterable

def cscan_head_movement(request_blocks: Iterable[int], head: int, disk_size: int) -> int:
    """Return one-direction C-SCAN head movement for requests on a circular disk.

    This simplified model services requests >= head, goes to the final cylinder,
    wraps to cylinder 0, then services requests below head. The wrap movement is
    counted. It is a teaching simulation, not a hardware latency prediction.
    """
    requests = sorted(set(int(x) for x in request_blocks))
    if not requests:
        return 0
    if any(x < 0 or x >= disk_size for x in requests):
        raise ValueError("Request block is outside the simulated disk.")
    if not 0 <= head < disk_size:
        raise ValueError("Head position is outside the simulated disk.")

    higher = [x for x in requests if x >= head]
    lower = [x for x in requests if x < head]

    movement = 0
    current = head
    for block in higher:
        movement += abs(block - current)
        current = block

    if lower:
        # Move to disk end, wrap to zero, then move to the lower requests.
        movement += (disk_size - 1 - current) if higher else 0
        movement += disk_size - 1
        current = 0
        for block in lower:
            movement += abs(block - current)
            current = block
    return movement

def estimate_latency_ms(blocks: list[int], head: int, disk_size: int,
                        movement_ms_per_block: float = 0.08,
                        transfer_ms_per_block: float = 0.15) -> float:
    """Simple estimate combining simulated movement and block-transfer costs."""
    if not blocks:
        return 0.0
    movement = cscan_head_movement(blocks, head, disk_size)
    return round(movement * movement_ms_per_block + len(blocks) * transfer_ms_per_block, 3)
