import math
import time
from collections import deque

from src.core.config import settings


class SlidingWindowRateLimiter:
    """Limitador de taxa em memória por janela deslizante para mitigação de força bruta."""

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
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
        bucket.append(now)
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
)

dono_login_rate_limiter = SlidingWindowRateLimiter(
    max_attempts=settings.OPERATIONAL_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=settings.OPERATIONAL_RATE_LIMIT_WINDOW_SECONDS,
)
