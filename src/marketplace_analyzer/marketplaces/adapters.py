"""Marketplace-specific adapter shells; endpoint parsing is configured explicitly."""

from marketplace_analyzer.domain.entities import ListingData
from marketplace_analyzer.marketplaces.base import RateLimitedHttpAdapter


class _ConfiguredAdapter(RateLimitedHttpAdapter):
    def _search(self, mode: str, value: str) -> list[ListingData]:
        if not self.base_url:
            raise RuntimeError(f"{self.marketplace} adapter devre dışı: uyumlu resmi endpoint yapılandırılmamış.")
        raise NotImplementedError("Endpoint yanıt şeması doğrulandıktan sonra adapter parser'ı eklenmelidir.")

    def fetch_by_barcode(self, barcode: str) -> list[ListingData]:
        return self._search("barcode", barcode)

    def fetch_by_oem(self, oem_number: str) -> list[ListingData]:
        return self._search("oem", oem_number)

    def search_keyword(self, query: str) -> list[ListingData]:
        return self._search("keyword", query)


class TrendyolAdapter(_ConfiguredAdapter):
    def __init__(self, **kwargs):
        super().__init__(marketplace="trendyol", **kwargs)


class HepsiburadaAdapter(_ConfiguredAdapter):
    def __init__(self, **kwargs):
        super().__init__(marketplace="hepsiburada", **kwargs)
