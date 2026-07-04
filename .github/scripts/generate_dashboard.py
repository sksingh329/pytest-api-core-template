"""
Maintains the gh-pages dashboard:
  1. Deletes run folders beyond a retention count, so the branch (and every
     CI checkout of it) doesn't grow unbounded as reports accumulate.
  2. Regenerates `index.html` listing the surviving reports, newest first.

Usage:
    python3 .github/scripts/generate_dashboard.py <gh-pages-checkout> [retention_count]

retention_count defaults to 200 runs kept on disk / listed on the dashboard.
"""
import datetime
import html
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1])
retention_count = int(sys.argv[2]) if len(sys.argv) > 2 else 200

runs_dir = root / "runs"
run_dirs = sorted(
    [p for p in runs_dir.iterdir() if p.is_dir()] if runs_dir.exists() else [],
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

stale_dirs = run_dirs[retention_count:]
for stale in stale_dirs:
    shutil.rmtree(stale)
if stale_dirs:
    print(f"Pruned {len(stale_dirs)} run(s) beyond retention count {retention_count}.")

reports = sorted(
    runs_dir.glob("*/*/*.html") if runs_dir.exists() else [],
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

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
  input#search {{ margin-top: 1rem; padding: 0.5rem 0.75rem; width: 100%; max-width: 24rem;
    background: #161b22; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #30363d; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>API Test Reports</h1>
<p>{len(reports)} report(s) published (showing up to {retention_count} most recent). Newest first.</p>
<input id="search" type="text" placeholder="Filter by report name or run id...">
<table id="report-table">
<tr><th>Report</th><th>Run</th><th>Published</th></tr>
{''.join(rows)}
</table>
<script>
  document.getElementById('search').addEventListener('input', function (e) {{
    var q = e.target.value.toLowerCase();
    var rows = document.querySelectorAll('#report-table tr:not(:first-child)');
    rows.forEach(function (row) {{
      row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    }});
  }});
</script>
</body>
</html>
"""

(root / "index.html").write_text(index_html)
print(f"Generated dashboard with {len(reports)} report(s).")
