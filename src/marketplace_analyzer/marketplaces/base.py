"""Shared compliant HTTP behavior for marketplace adapters."""

import logging
import random
import time
from urllib.robotparser import RobotFileParser

from marketplace_analyzer.domain.ports import MarketplaceAdapter

logger = logging.getLogger(__name__)


class MarketplaceBlockedError(RuntimeError):
    """Raised when a marketplace denies automated access."""


class RateLimitedHttpAdapter(MarketplaceAdapter):
    """Base class implementing robots checks and bounded retry behavior."""

    def __init__(self, marketplace: str, base_url: str, user_agents: list[str], timeout: float = 15,
                 max_retries: int = 4, backoff_base: float = 1, backoff_max: float = 30):
        self.marketplace = marketplace
        self.base_url = base_url.rstrip("/")
        self.user_agents = user_agents
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max

    def _check_robots(self, url: str, user_agent: str) -> None:
        parts = url.split("/", 3)
        parser = RobotFileParser()
        parser.set_url(parts[0] + "//" + parts[2] + "/robots.txt")
        try:
            parser.read()
        except Exception as exc:
            logger.warning("robots.txt okunamadı; istek durduruldu", extra={"marketplace": self.marketplace, "error": str(exc)})
            raise MarketplaceBlockedError("robots.txt doğrulanamadığı için veri isteği durduruldu.") from exc
        if not parser.can_fetch(user_agent, url):
            raise MarketplaceBlockedError("robots.txt otomatik erişime izin vermiyor.")

    def _get_json(self, url: str, params: dict[str, str] | None = None):
        if not self.user_agents:
            raise ValueError("En az bir User-Agent yapılandırılmalıdır.")
        import requests
        user_agent = random.choice(self.user_agents)
        self._check_robots(url, user_agent)
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=self.timeout, headers={"User-Agent": user_agent})
                if response.status_code in (403, 429) or "cloudflare" in response.text[:1000].casefold():
                    logger.error("Marketplace erişimi engellendi", extra={"marketplace": self.marketplace, "status": response.status_code})
                    raise MarketplaceBlockedError("Pazaryeri erişimi engelledi; otomatik deneme durduruldu.")
                if response.status_code >= 500 and attempt < self.max_retries:
                    self._backoff(attempt)
                    continue
                response.raise_for_status()
                return response.json()
            except MarketplaceBlockedError:
                raise
            except requests.RequestException:
                if attempt >= self.max_retries:
                    logger.exception("Pazaryeri isteği başarısız", extra={"marketplace": self.marketplace})
                    raise
                self._backoff(attempt)
        raise MarketplaceBlockedError("Yeniden deneme sınırı aşıldı.")

    def _backoff(self, attempt: int) -> None:
        delay = min(self.backoff_max, self.backoff_base * (2 ** attempt))
        time.sleep(random.uniform(delay * 0.5, delay))
