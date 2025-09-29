from __future__ import annotations
from typing import Iterable, Set, Deque
from collections import deque

class Frontier:
    """FIFO URL frontier with a seen set."""
    def __init__(self, seeds: Iterable[str]):
        self.queue: Deque[str] = deque(seeds)
        self.seen: Set[str] = set(seeds)

    def push(self, url: str) -> None:
        if url not in self.seen:
            self.seen.add(url)
            self.queue.append(url)

    def pop(self) -> str | None:
        return self.queue.popleft() if self.queue else None

    def __len__(self) -> int:
        return len(self.queue)