"""Generate sitemap.xml for Google Search Console submission."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.seo import build_sitemap_entries, render_sitemap_xml, site_base_url


class Command(BaseCommand):
    help = "Generate sitemap.xml (home, Surat SEO pages, business listings, booking)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            default="",
            help="Output path (default: static/sitemap.xml)",
        )

    def handle(self, *args, **options):
        out = options["out"]
        if not out:
            out = str(Path(settings.BASE_DIR) / "static" / "sitemap.xml")

        entries = build_sitemap_entries()
        xml = render_sitemap_xml(entries)
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(xml, encoding="utf-8")

        base = site_base_url()
        self.stdout.write(self.style.SUCCESS(f"Wrote {len(entries)} URLs → {path}"))
        self.stdout.write("")
        self.stdout.write("Google Search Console:")
        self.stdout.write(f"  1. Open https://search.google.com/search-console")
        self.stdout.write(f"  2. Property: {base}")
        self.stdout.write(f"  3. Sitemaps → submit: {base}/sitemap.xml")
        self.stdout.write("")
        self.stdout.write(f"Live sitemap (preferred): {base}/sitemap.xml")
        self.stdout.write(f"robots.txt points to:     {base}/robots.txt")
