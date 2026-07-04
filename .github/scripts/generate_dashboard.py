"""
Regenerates the gh-pages dashboard `index.html` by scanning every published
report under `runs/*/*/*.html` and listing them newest-first.

Run from the repo root with the gh-pages checkout as the only argument:
    python3 .github/scripts/generate_dashboard.py /path/to/gh-pages-checkout
"""
import datetime
import html
import sys
from pathlib import Path

root = Path(sys.argv[1])
runs_dir = root / "runs"
reports = sorted(
    runs_dir.glob("*/*/*.html"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
) if runs_dir.exists() else []

rows = []
for path in reports:
    rel = path.relative_to(root)
    run_slug = rel.parts[1]
    published = datetime.datetime.fromtimestamp(
        path.stat().st_mtime, tz=datetime.timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC")
    rows.append(
        f"<tr><td><a href=\"/{html.escape(rel.as_posix())}\">{html.escape(rel.name)}</a></td>"
        f"<td>{html.escape(run_slug)}</td><td>{published}</td></tr>"
    )

index_html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>API Test Reports</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; background: #0d1117; color: #e6edf3; }}
  h1 {{ font-size: 1.4rem; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #30363d; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>API Test Reports</h1>
<p>{len(reports)} report(s) published. Newest first.</p>
<table>
<tr><th>Report</th><th>Run</th><th>Published</th></tr>
{''.join(rows)}
</table>
</body>
</html>
"""

(root / "index.html").write_text(index_html)
print(f"Generated dashboard with {len(reports)} report(s).")
