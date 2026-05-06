from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px


def run_data_quality_checks(df: pd.DataFrame) -> list[str]:
    failures: list[str] = []

    if df.empty:
        failures.append("No rows returned from incremental API pull.")
        return failures

    if df["unique_key"].isna().any():
        failures.append("unique_key contains null values.")

    if df["unique_key"].duplicated().any():
        failures.append("unique_key contains duplicates.")

    if df["created_date"].isna().any():
        failures.append("created_date contains null values.")

    invalid_borough = (~df["borough"].isin(["BROOKLYN", "BRONX", "MANHATTAN", "QUEENS", "STATEN ISLAND"])) & (
        df["borough"].notna()
    )
    if invalid_borough.any():
        failures.append("borough contains unexpected values.")

    return failures


def generate_outputs(
    metrics_df: pd.DataFrame,
    complaints_df: pd.DataFrame,
    borough_trends_df: pd.DataFrame,
    open_vs_closed_df: pd.DataFrame,
    top_agencies_df: pd.DataFrame,
    quality_failures: list[str],
    markdown_path: Path,
    metrics_csv_path: Path,
    html_path: Path,
    charts_dir: Path,
) -> None:
    metrics_df.to_csv(metrics_csv_path, index=False)

    chart_files = _build_charts(
        complaints_df=complaints_df,
        borough_trends_df=borough_trends_df,
        open_vs_closed_df=open_vs_closed_df,
        top_agencies_df=top_agencies_df,
        charts_dir=charts_dir,
    )
    _write_png_screenshots(
        complaints_df=complaints_df,
        borough_trends_df=borough_trends_df,
        open_vs_closed_df=open_vs_closed_df,
        top_agencies_df=top_agencies_df,
        charts_dir=charts_dir,
    )

    status_line = "✅ PASS" if not quality_failures else "❌ FAIL"
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    _write_daily_summary_md(
        markdown_path=markdown_path,
        metrics_df=metrics_df,
        quality_failures=quality_failures,
        status_line=status_line,
        run_date=run_date,
    )
    _write_html_report(
        html_path=html_path,
        metrics_df=metrics_df,
        chart_files=chart_files,
        quality_failures=quality_failures,
        status_line=status_line,
        run_date=run_date,
    )


def update_readme(
    readme_path: Path,
    metrics_df: pd.DataFrame,
    quality_failures: list[str],
) -> None:
    """Inject the latest pipeline summary into README.md between sentinel comments."""
    status_icon = "✅ PASS" if not quality_failures else "❌ FAIL"
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    summary_lines = [
        "<!-- PIPELINE-SUMMARY-START -->",
        "",
        "## 📊 Latest Pipeline Run",
        "",
        f"**Run date:** {run_date}  ",
        f"**Data quality status:** {status_icon}  ",
        "",
        "### Last 7 Days – Volume & Status",
        "",
        _to_markdown_table(metrics_df),
        "",
        "### Charts",
        "",
        "| Chart | Link |",
        "| --- | --- |",
        "| Top 10 Complaint Types | [view](reports/charts/top_complaints.html) |",
        "| Borough Trends (7 days) | [view](reports/charts/borough_trends.html) |",
        "| Open vs Closed Over Time | [view](reports/charts/open_vs_closed.html) |",
        "| Top Agencies | [view](reports/charts/top_agencies.html) |",
        "",
        "### Chart Screenshots",
        "",
        "#### Top 10 Complaint Types",
        "[Interactive chart](reports/charts/top_complaints.html)",
        "",
        "![Top 10 Complaint Types](reports/charts/top_complaints.png)",
        "",
        "#### Borough Trends (7 days)",
        "[Interactive chart](reports/charts/borough_trends.html)",
        "",
        "![Borough Trends (7 days)](reports/charts/borough_trends.png)",
        "",
        "#### Open vs Closed Over Time",
        "[Interactive chart](reports/charts/open_vs_closed.html)",
        "",
        "![Open vs Closed Over Time](reports/charts/open_vs_closed.png)",
        "",
        "#### Top Agencies",
        "[Interactive chart](reports/charts/top_agencies.html)",
        "",
        "![Top Agencies](reports/charts/top_agencies.png)",
        "",
        "_Charts are interactive HTML files with PNG screenshots saved for README preview._",
        "",
        "<!-- PIPELINE-SUMMARY-END -->",
    ]
    summary_block = "\n".join(summary_lines)

    content = readme_path.read_text(encoding="utf-8")

    start_marker = "<!-- PIPELINE-SUMMARY-START -->"
    end_marker = "<!-- PIPELINE-SUMMARY-END -->"

    if start_marker in content and end_marker in content:
        before = content[: content.index(start_marker)]
        after = content[content.index(end_marker) + len(end_marker) :]
        new_content = before + summary_block + after
    else:
        new_content = content.rstrip() + "\n\n" + summary_block + "\n"

    readme_path.write_text(new_content, encoding="utf-8")


def _build_charts(
    complaints_df: pd.DataFrame,
    borough_trends_df: pd.DataFrame,
    open_vs_closed_df: pd.DataFrame,
    top_agencies_df: pd.DataFrame,
    charts_dir: Path,
) -> dict[str, dict[str, Path | str | None]]:
    chart_files: dict[str, dict[str, Path | str | None]] = {}

    # 1. Top complaint types
    if not complaints_df.empty:
        fig = px.bar(
            complaints_df.sort_values("count"),
            x="count",
            y="complaint_type",
            orientation="h",
            title="Top 10 Complaint Types (most recent day)",
            labels={"count": "Requests", "complaint_type": "Complaint Type"},
            color="count",
            color_continuous_scale="Blues",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        chart_files["top_complaints"] = _write_chart_assets(
            fig=fig,
            charts_dir=charts_dir,
            stem="top_complaints",
            label="Top Complaint Types",
        )

    # 2. Borough trends over the last 7 days
    if not borough_trends_df.empty:
        fig = px.line(
            borough_trends_df,
            x="request_date",
            y="count",
            color="borough",
            markers=True,
            title="Borough Request Trends (Last 7 Days)",
            labels={"request_date": "Date", "count": "Requests", "borough": "Borough"},
        )
        chart_files["borough_trends"] = _write_chart_assets(
            fig=fig,
            charts_dir=charts_dir,
            stem="borough_trends",
            label="Borough Trends",
        )

    # 3. Open vs. Closed over time
    if not open_vs_closed_df.empty:
        fig = px.area(
            open_vs_closed_df,
            x="request_date",
            y="count",
            color="status",
            title="Open vs Closed Requests Over Time (Last 7 Days)",
            labels={"request_date": "Date", "count": "Requests", "status": "Status"},
            color_discrete_map={"Closed": "#2ecc71", "Open": "#e74c3c"},
        )
        chart_files["open_vs_closed"] = _write_chart_assets(
            fig=fig,
            charts_dir=charts_dir,
            stem="open_vs_closed",
            label="Open Vs Closed",
        )

    # 4. Top agencies
    if not top_agencies_df.empty:
        fig = px.bar(
            top_agencies_df.sort_values("count"),
            x="count",
            y="agency_name",
            orientation="h",
            title="Top Responding Agencies (most recent day)",
            labels={"count": "Requests", "agency_name": "Agency"},
            color="count",
            color_continuous_scale="Oranges",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        chart_files["top_agencies"] = _write_chart_assets(
            fig=fig,
            charts_dir=charts_dir,
            stem="top_agencies",
            label="Top Agencies",
        )

    return chart_files


def _write_daily_summary_md(
    markdown_path: Path,
    metrics_df: pd.DataFrame,
    quality_failures: list[str],
    status_line: str,
    run_date: str,
) -> None:
    md_lines = [
        "# NYC 311 Daily Summary",
        "",
        f"**Run date:** {run_date}",
        f"**Data quality status:** {status_line}",
        "",
        "## Last 7 Days – Volume & Status",
        "",
        _to_markdown_table(metrics_df),
        "",
        "## Data Quality Checks",
    ]

    if quality_failures:
        md_lines.extend([f"- ❌ {item}" for item in quality_failures])
    else:
        md_lines.append("- ✅ All checks passed.")

    md_lines.extend(
        [
            "",
            "## Charts",
            "",
            "| Chart | File |",
            "| --- | --- |",
            "| Top 10 Complaint Types | `reports/charts/top_complaints.html` |",
            "| Borough Trends (7 days) | `reports/charts/borough_trends.html` |",
            "| Open vs Closed Over Time | `reports/charts/open_vs_closed.html` |",
            "| Top Agencies | `reports/charts/top_agencies.html` |",
        ]
    )

    markdown_path.write_text("\n".join(md_lines), encoding="utf-8")


def _write_html_report(
    html_path: Path,
    metrics_df: pd.DataFrame,
    chart_files: dict[str, dict[str, Path | str | None]],
    quality_failures: list[str],
    status_line: str,
    run_date: str,
) -> None:
    chart_links = ""
    chart_images = ""
    for _, asset in chart_files.items():
        html_path = asset["html"]
        png_path = asset["png"]
        label = str(asset["label"])
        chart_links += f"<li><a href='charts/{Path(str(html_path)).name}'>{label}</a></li>\n"

        if png_path and Path(str(png_path)).exists():
            chart_images += (
                f"<h3>{label}</h3>"
                f"<p><a href='charts/{Path(str(html_path)).name}'>Open interactive chart</a></p>"
                f"<img src='charts/{Path(str(png_path)).name}' alt='{label}' style='max-width:100%; border:1px solid #ddd;'>"
            )

    qc_items = ""
    if quality_failures:
        qc_items = "".join(f"<li>❌ {item}</li>" for item in quality_failures)
    else:
        qc_items = "<li>✅ All checks passed.</li>"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>NYC 311 Daily Summary</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f4f4f4; }}
    tr:nth-child(even) {{ background-color: #fafafa; }}
    .pass {{ color: green; font-weight: bold; }}
    .fail {{ color: red; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>NYC 311 Daily Summary</h1>
  <p>Run date: <strong>{run_date}</strong></p>
  <p>Data quality status: <span class="{'pass' if 'PASS' in status_line else 'fail'}">{status_line}</span></p>

  <h2>Last 7 Days – Volume &amp; Status</h2>
  {metrics_df.to_html(index=False)}

  <h2>Data Quality Checks</h2>
  <ul>{qc_items}</ul>

  <h2>Charts</h2>
  <ul>{chart_links}</ul>

  <h2>Chart Screenshots</h2>
  {chart_images}
</body>
</html>"""
    html_path.write_text(html, encoding="utf-8")


def _write_chart_assets(fig, charts_dir: Path, stem: str, label: str) -> dict[str, Path | str | None]:
    html_path = charts_dir / f"{stem}.html"
    png_path = charts_dir / f"{stem}.png"

    fig.write_html(str(html_path), include_plotlyjs="cdn")

    return {
        "label": label,
        "html": html_path,
        "png": png_path,
    }


def _write_png_screenshots(
    complaints_df: pd.DataFrame,
    borough_trends_df: pd.DataFrame,
    open_vs_closed_df: pd.DataFrame,
    top_agencies_df: pd.DataFrame,
    charts_dir: Path,
) -> None:
    if not complaints_df.empty:
        fig, ax = plt.subplots(figsize=(12, 7))
        sorted_df = complaints_df.sort_values("count")
        ax.barh(sorted_df["complaint_type"], sorted_df["count"], color="#3b82f6")
        ax.set_title("Top 10 Complaint Types (most recent day)")
        ax.set_xlabel("Requests")
        fig.tight_layout()
        fig.savefig(charts_dir / "top_complaints.png", dpi=150)
        plt.close(fig)

    if not borough_trends_df.empty:
        fig, ax = plt.subplots(figsize=(12, 7))
        trend_df = borough_trends_df.copy()
        trend_df["request_date"] = pd.to_datetime(trend_df["request_date"])
        for borough, group in trend_df.groupby("borough"):
            group = group.sort_values("request_date")
            ax.plot(group["request_date"], group["count"], marker="o", label=borough)
        ax.set_title("Borough Request Trends (Last 7 Days)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Requests")
        ax.legend(loc="best", fontsize=8)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(charts_dir / "borough_trends.png", dpi=150)
        plt.close(fig)

    if not open_vs_closed_df.empty:
        fig, ax = plt.subplots(figsize=(12, 7))
        pivot_df = open_vs_closed_df.pivot_table(
            index="request_date", columns="status", values="count", aggfunc="sum", fill_value=0
        )
        pivot_df.index = pd.to_datetime(pivot_df.index)
        pivot_df = pivot_df.sort_index()
        pivot_df.plot.area(ax=ax, stacked=True, alpha=0.8)
        ax.set_title("Open vs Closed Requests Over Time (Last 7 Days)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Requests")
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(charts_dir / "open_vs_closed.png", dpi=150)
        plt.close(fig)

    if not top_agencies_df.empty:
        fig, ax = plt.subplots(figsize=(12, 7))
        sorted_df = top_agencies_df.sort_values("count")
        ax.barh(sorted_df["agency_name"], sorted_df["count"], color="#f97316")
        ax.set_title("Top Responding Agencies (most recent day)")
        ax.set_xlabel("Requests")
        fig.tight_layout()
        fig.savefig(charts_dir / "top_agencies.png", dpi=150)
        plt.close(fig)


def _to_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No metrics available yet._"

    headers = [str(col) for col in df.columns]
    divider = ["---" for _ in headers]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(divider) + " |"]

    for _, record in df.iterrows():
        values = [str(record[col]) for col in df.columns]
        rows.append("| " + " | ".join(values) + " |")

    return "\n".join(rows)
