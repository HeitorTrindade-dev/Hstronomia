import math
import time
from collections import deque

from src.core.config import settings


class SlidingWindowRateLimiter:
    """Limitador de taxa em memória por janela deslizante para mitigação de força bruta."""

    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        max_keys: int = 10000,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.max_keys = max(1, max_keys)
        self._attempts: dict[str, deque[float]] = {}

    def _prune(self, key: str, now: float) -> deque[float]:
        bucket = self._attempts.get(key)
        if bucket is None:
            return deque()

        cutoff = now - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if not bucket:
            self._attempts.pop(key, None)
            return deque()

        return bucket

    def _evict_if_full(self, now: float) -> None:
        if len(self._attempts) < self.max_keys:
            return

        # 1. Remove chaves já expiradas em toda a tabela
        cutoff = now - self.window_seconds
        expired_keys = [
            k for k, b in self._attempts.items() if not b or b[-1] <= cutoff
        ]
        for k in expired_keys:
            self._attempts.pop(k, None)

        # 2. Se ainda estiver no limite, remove as chaves mais antigas (FIFO no dict)
        while len(self._attempts) >= self.max_keys:
            oldest_key = next(iter(self._attempts))
            self._attempts.pop(oldest_key, None)

    def is_blocked(self, key: str) -> tuple[bool, int]:
        """Retorna (bloqueado, segundos_para_tentar_novamente)."""
        now = time.monotonic()
        bucket = self._prune(key, now)
        if len(bucket) >= self.max_attempts:
            retry_after = max(1, math.ceil(self.window_seconds - (now - bucket[0])))
            return True, retry_after
        return False, 0

    def record_failure(self, key: str) -> int:
        """Registra tentativa falha e retorna o total na janela atual."""
        now = time.monotonic()
        bucket = self._prune(key, now)
        if key not in self._attempts:
            self._evict_if_full(now)
        bucket.append(now)
        # Reinsere para atualizar ordem LRU/inserção no dict
        self._attempts.pop(key, None)
        self._attempts[key] = bucket
        return len(bucket)

    def reset_key(self, key: str) -> None:
        """Remove o histórico de falhas após autenticação bem-sucedida."""
        self._attempts.pop(key, None)

    def clear(self) -> None:
        """Limpa todos os contadores (útil para isolamento de testes)."""
        self._attempts.clear()


operational_login_rate_limiter = SlidingWindowRateLimiter(
    max_attempts=settings.OPERATIONAL_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=settings.OPERATIONAL_RATE_LIMIT_WINDOW_SECONDS,
    max_keys=settings.OPERATIONAL_RATE_LIMIT_MAX_KEYS,
)

dono_login_rate_limiter = SlidingWindowRateLimiter(
    max_attempts=settings.OPERATIONAL_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=settings.OPERATIONAL_RATE_LIMIT_WINDOW_SECONDS,
    max_keys=settings.OPERATIONAL_RATE_LIMIT_MAX_KEYS,
)
