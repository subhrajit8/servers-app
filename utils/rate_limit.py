from math import ceil
from time import monotonic

from fastapi import HTTPException, status

LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW_SECONDS = 30
MAX_TRACKED_CLIENTS = 10_000


class LoginRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[str, tuple[float, int]] = {}

    async def check(self, client_ip: str) -> None:
        now = monotonic()
        expired_clients = [
            ip
            for ip, (window_start, _) in self._attempts.items()
            if now - window_start >= LOGIN_RATE_WINDOW_SECONDS
        ]
        for ip in expired_clients:
            del self._attempts[ip]

        attempt = self._attempts.get(client_ip)
        if attempt is None:
            if len(self._attempts) >= MAX_TRACKED_CLIENTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts. Try again later.",
                    headers={"Retry-After": str(LOGIN_RATE_WINDOW_SECONDS)},
                )
            self._attempts[client_ip] = (now, 1)
            return

        window_start, count = attempt
        if count >= LOGIN_RATE_LIMIT:
            retry_after = max(
                1,
                ceil(LOGIN_RATE_WINDOW_SECONDS - (now - window_start)),
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        self._attempts[client_ip] = (window_start, count + 1)


login_rate_limiter = LoginRateLimiter()
