"""
ReportRegistry for code-first reports in Django ReportCraft.
Provides central catalog registration and retrieval for in-memory CodeReport instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from reportcraft.code.report import CodeReport


class CatalogItem(dict):
    """
    Dictionary representation of a registered code report item in the catalog.
    Supports both dict key lookup (item['title']) and attribute access (item.title).
    """

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'CatalogItem' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class ReportRegistry:
    """
    Central registry for code-first reports.
    """

    def __init__(self) -> None:
        self._registry: dict[str, dict[str, Any]] = {}

    def register(
        self,
        report: CodeReport | None = None,
        in_catalog: bool = True,
        section: str | None = None,
        url: str | None = None,
    ) -> Any:
        """
        Register a CodeReport instance with the registry.
        Supports both function call and decorator syntax:
            site.register(report, in_catalog=True, section="finance", url="/custom/")
            @site.register
            @site.register(in_catalog=False)
        """
        def _register(rep: CodeReport) -> CodeReport:
            slug = getattr(rep, "slug", None)
            if not slug:
                raise ValueError("A CodeReport must have a non-empty 'slug' to be registered.")
            self._registry[slug] = {
                "report": rep,
                "in_catalog": in_catalog,
                "section": section,
                "url": url,
            }
            return rep

        if report is not None:
            return _register(report)
        return _register

    def unregister(self, slug: str | CodeReport) -> None:
        """
        Remove a report from the registry by its slug or report instance.
        """
        if hasattr(slug, "slug"):
            slug = slug.slug
        self._registry.pop(slug, None)

    def get_report(self, slug: str) -> CodeReport | None:
        """
        Retrieve a registered CodeReport by slug.
        """
        entry = self._registry.get(slug)
        if entry is not None:
            return entry["report"]
        return None

    def get_catalog_items(self, section: str | None = None) -> list[dict]:
        """
        Return a list of catalog item dictionaries for registered reports where in_catalog is True.
        Optionally filters by section. If section is None, returns all in_catalog reports.
        """
        items: list[dict] = []
        for slug, entry in self._registry.items():
            if not entry.get("in_catalog", True):
                continue

            report = entry["report"]
            report_section = entry.get("section")
            if report_section is None:
                report_section = getattr(report, "section", None)

            if section is not None and report_section != section:
                continue

            item = CatalogItem(
                slug=slug,
                title=getattr(report, "title", "") or slug,
                description=getattr(report, "description", ""),
                section=report_section,
                url=entry.get("url"),
                in_catalog=True,
                report=report,
            )
            items.append(item)
        return items

    def clear(self) -> None:
        """
        Clear all registered reports from the registry.
        """
        self._registry.clear()


site = ReportRegistry()

__all__ = ["CatalogItem", "ReportRegistry", "site"]
