import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))


def _rel_luminance(rgb):
    def f(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    la = _rel_luminance(_hex_to_rgb(hex_a))
    lb = _rel_luminance(_hex_to_rgb(hex_b))
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


class Command(BaseCommand):
    help = "Basic accessibility/contrast sanity checks for SquadUp theme."

    def handle(self, *args, **options):
        css_path = Path(settings.BASE_DIR) / "static" / "css" / "theme.css"
        if not css_path.exists():
            self.stderr.write(self.style.ERROR(f"Missing theme CSS: {css_path}"))
            return

        css = css_path.read_text(encoding="utf-8", errors="ignore")
        vars_found = dict(
            re.findall(r"--([a-zA-Z0-9\-_]+)\s*:\s*(#[0-9a-fA-F]{3,6})\s*;", css)
        )

        needed = {
            "text": vars_found.get("text"),
            "muted": vars_found.get("muted"),
            "bg": vars_found.get("bg"),
            "surface": vars_found.get("surface"),
            "accent": vars_found.get("accent"),
        }

        missing = [k for k, v in needed.items() if not v]
        if missing:
            self.stderr.write(
                self.style.WARNING(f"Could not find CSS vars: {', '.join(missing)}")
            )

        pairs = [
            ("text on surface", needed["text"], needed["surface"], 4.5),
            ("muted on surface", needed["muted"], needed["surface"], 4.5),
            ("accent on surface", needed["accent"], needed["surface"], 3.0),
            ("text on bg", needed["text"], needed["bg"], 4.5),
        ]

        self.stdout.write("Contrast ratios (WCAG AA targets):")
        ok = True
        for label, fg, bg, target in pairs:
            if not fg or not bg:
                continue
            ratio = _contrast_ratio(fg, bg)
            status = "OK" if ratio >= target else "LOW"
            if status == "LOW":
                ok = False
            self.stdout.write(f"- {label}: {ratio:.2f}:1 (target {target}:1) [{status}]")

        if ok:
            self.stdout.write(self.style.SUCCESS("A11y contrast checks look good."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Some contrast ratios are low; consider brightening text/muted colors."
                )
            )
