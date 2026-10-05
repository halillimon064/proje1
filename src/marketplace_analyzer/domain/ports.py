"""Interfaces that keep the application independent of infrastructure."""

from abc import ABC, abstractmethod

from marketplace_analyzer.domain.entities import ListingData


class MarketplaceAdapter(ABC):
    """Minimal marketplace search contract."""

    marketplace: str

    @abstractmethod
    def fetch_by_barcode(self, barcode: str) -> list[ListingData]:
        """Find listings by exact barcode."""

    @abstractmethod
    def fetch_by_oem(self, oem_number: str) -> list[ListingData]:
        """Find listings by manufacturer part number."""

    @abstractmethod
    def search_keyword(self, query: str) -> list[ListingData]:
        """Search listings using a free-text query."""


class ProductImporter(ABC):
    """Interface for supplier product sources."""

    @abstractmethod
    def import_file(self, path: str) -> object:
        """Read and validate a supplier file."""
