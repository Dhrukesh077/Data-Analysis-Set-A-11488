"""Delivery Delay Analysis - reproducible Python pipeline.

Run from the repository root:

    python python/analysis.py

Reads  : data/raw/deliveries.csv, data/raw/routes.csv  (never modified)
Writes : outputs/clean_data.csv
         outputs/python_summary.csv            (service-type summary)
         outputs/python_hub_summary.csv
         outputs/python_route_summary.csv
         outputs/python_monthly_summary.csv
         outputs/python_chart.png              (monthly total delay days)

Metric definitions (identical in Excel, SQL and Power BI):
    delay_days            = MAX(actual_days - promised_days, 0)
    delayed record        = actual_days > promised_days
    delay incidence rate  = delayed records / total records * 100
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend: works without a display
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

# --------------------------------------------------------------------------- #
# Paths and constants
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
OUT_DIR = REPO_ROOT / "outputs"

DELIVERIES_FILE = RAW_DIR / "deliveries.csv"
ROUTES_FILE = RAW_DIR / "routes.csv"

DELIVERIES_COLUMNS = ["record_id", "month", "route_id", "hub", "promised_days", "actual_days"]
ROUTES_COLUMNS = ["route_id", "route", "service_type"]
MONTH_ORDER = ["Jan", "Feb", "Mar"]

EXPECTED_RAW_DELIVERY_ROWS = 13
EXPECTED_CLEAN_DELIVERY_ROWS = 12
EXPECTED_ROUTE_ROWS = 4
EXPECTED_DUPLICATES = 1

TEXT_COLS_DELIVERIES = ["month", "route_id", "hub"]
TEXT_COLS_ROUTES = ["route_id", "route", "service_type"]


# --------------------------------------------------------------------------- #
# Loading and validation
# --------------------------------------------------------------------------- #
def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file (used to prove raw data is untouched)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_data(
    deliveries_path: Path = DELIVERIES_FILE, routes_path: Path = ROUTES_FILE
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read both raw CSV files as UTF-8 without any alteration."""
    for p in (deliveries_path, routes_path):
        if not p.exists():
            raise FileNotFoundError(
                f"Missing input file: {p}. Run the script from the repository root "
                "and make sure data/raw/ contains deliveries.csv and routes.csv."
            )
    deliveries = pd.read_csv(deliveries_path, encoding="utf-8")
    routes = pd.read_csv(routes_path, encoding="utf-8")
    return deliveries, routes


def validate_raw_data(deliveries: pd.DataFrame, routes: pd.DataFrame) -> dict:
    """Validate the raw inputs against the documented source specification.

    Raises ValueError with an informative message on any violation and returns a
    dictionary of validation facts that is printed in the run log.
    """
    if list(deliveries.columns) != DELIVERIES_COLUMNS:
        raise ValueError(f"deliveries.csv columns {list(deliveries.columns)} != {DELIVERIES_COLUMNS}")
    if list(routes.columns) != ROUTES_COLUMNS:
        raise ValueError(f"routes.csv columns {list(routes.columns)} != {ROUTES_COLUMNS}")
    if len(deliveries) != EXPECTED_RAW_DELIVERY_ROWS:
        raise ValueError(f"Expected {EXPECTED_RAW_DELIVERY_ROWS} raw delivery rows, found {len(deliveries)}")
    if len(routes) != EXPECTED_ROUTE_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROUTE_ROWS} route rows, found {len(routes)}")

    # Missing values and dtypes
    if deliveries.isna().any().any() or routes.isna().any().any():
        raise ValueError("Unexpected missing values in the raw data; refusing to impute.")
    if not pd.api.types.is_integer_dtype(deliveries["record_id"]):
        raise ValueError("record_id must be an integer column")
    for col in ("promised_days", "actual_days"):
        if not pd.api.types.is_numeric_dtype(deliveries[col]):
            raise ValueError(f"{col} must be numeric")
    for col in TEXT_COLS_DELIVERIES:
        if not (deliveries[col].map(type) == str).all():
            raise ValueError(f"{col} must be text")
    for col in TEXT_COLS_ROUTES:
        if not (routes[col].map(type) == str).all():
            raise ValueError(f"{col} (routes) must be text")

    # Duplicates: exactly one exact duplicate row is expected
    dup_count = int(deliveries.duplicated(keep="first").sum())
    if dup_count != EXPECTED_DUPLICATES:
        raise ValueError(f"Expected {EXPECTED_DUPLICATES} exact duplicate row, found {dup_count}")

    # route_id must be a unique lookup key
    if not routes["route_id"].is_unique:
        raise ValueError("routes.route_id must be unique (lookup key)")

    # record_id must be unique once the duplicate is removed
    if not deliveries.drop_duplicates()["record_id"].is_unique:
        raise ValueError("record_id is not unique after duplicate removal")

    if not set(deliveries["month"]).issubset(MONTH_ORDER):
        raise ValueError(f"Unexpected month values: {sorted(set(deliveries['month']) - set(MONTH_ORDER))}")

    return {
        "raw_delivery_rows": len(deliveries),
        "route_rows": len(routes),
        "exact_duplicate_rows": dup_count,
    }


# --------------------------------------------------------------------------- #
# Cleaning, merging, metrics
# --------------------------------------------------------------------------- #
def clean_deliveries(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows (keep the first occurrence); keep every other record."""
    clean = deliveries.drop_duplicates(keep="first").reset_index(drop=True)
    if len(clean) != EXPECTED_CLEAN_DELIVERY_ROWS:
        raise ValueError(f"Expected {EXPECTED_CLEAN_DELIVERY_ROWS} clean rows, found {len(clean)}")
    return clean


def merge_routes(clean: pd.DataFrame, routes: pd.DataFrame) -> pd.DataFrame:
    """Left-join the route lookup onto the clean deliveries and verify join integrity."""
    merged = clean.merge(routes, on="route_id", how="left", validate="many_to_one")
    if len(merged) != EXPECTED_CLEAN_DELIVERY_ROWS:
        raise ValueError(f"Join changed the row count: {len(merged)}")
    if not merged["service_type"].notna().all():
        unmatched = merged.loc[merged["service_type"].isna(), "route_id"].unique().tolist()
        raise ValueError(f"Unmatched route_id values after merge: {unmatched}")
    return merged


def calculate_metrics(merged: pd.DataFrame) -> pd.DataFrame:
    """Add delay_days and an is_delayed flag; month becomes an ordered categorical."""
    df = merged.copy()
    df["delay_days"] = (df["actual_days"] - df["promised_days"]).clip(lower=0)
    df["is_delayed"] = df["actual_days"] > df["promised_days"]
    df["month"] = pd.Categorical(df["month"], categories=MONTH_ORDER, ordered=True)
    if not df["delay_days"].ge(0).all():
        raise ValueError("Negative delay_days detected")
    return df


# --------------------------------------------------------------------------- #
# Summaries (rates always computed from underlying counts)
# --------------------------------------------------------------------------- #
def _summarise(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    g = df.groupby(keys, observed=True, sort=False)
    out = g.agg(
        delivery_count=("record_id", "count"),
        delayed_count=("is_delayed", "sum"),
        total_delay_days=("delay_days", "sum"),
    ).reset_index()
    out["delayed_count"] = out["delayed_count"].astype(int)
    out["delay_incidence_rate"] = (out["delayed_count"] / out["delivery_count"] * 100).round(2)
    return out


def build_service_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = _summarise(df, ["service_type"])
    return out.sort_values(["total_delay_days", "service_type"], ascending=[False, True]).reset_index(drop=True)


def build_hub_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = _summarise(df, ["hub"])
    return out.sort_values(["total_delay_days", "hub"], ascending=[False, True]).reset_index(drop=True)


def build_route_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = _summarise(df, ["route_id", "route", "service_type"])
    cols = ["route_id", "route", "service_type", "delivery_count", "delayed_count",
            "total_delay_days", "delay_incidence_rate"]
    out = out[cols]
    total = out["total_delay_days"].sum()
    out["share_of_total_delay_pct"] = (out["total_delay_days"] / total * 100).round(2)
    return out.sort_values(["total_delay_days", "route_id"], ascending=[False, True]).reset_index(drop=True)


def build_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = _summarise(df, ["month"])
    out = out.sort_values("month").reset_index(drop=True)  # categorical order Jan, Feb, Mar
    out["month"] = out["month"].astype(str)
    return out


def overall_metrics(df: pd.DataFrame) -> dict:
    """Overall KPIs from underlying counts (never by averaging subgroup rates)."""
    n = len(df)
    delayed = int(df["is_delayed"].sum())
    return {
        "delivery_count": n,
        "delayed_count": delayed,
        "total_delay_days": float(df["delay_days"].sum()),
        "delay_incidence_rate": round(delayed / n * 100, 2),
    }


def reconcile_summaries(df, service, hub, route, monthly) -> None:
    """Internal consistency check: every grouping must sum to the same total."""
    total = df["delay_days"].sum()
    for name, s in (("service", service), ("hub", hub), ("route", route), ("monthly", monthly)):
        if s["total_delay_days"].sum() != total:
            raise ValueError(f"{name} summary total {s['total_delay_days'].sum()} != overall {total}")
        if s["delivery_count"].sum() != len(df):
            raise ValueError(f"{name} summary delivery_count does not sum to {len(df)}")


# --------------------------------------------------------------------------- #
# Chart and export
# --------------------------------------------------------------------------- #
def create_monthly_chart(monthly: pd.DataFrame, path: Path) -> None:
    """Column chart of total delay days per month, ordered Jan -> Feb -> Mar."""
    fig, ax = plt.subplots(figsize=(8, 5), dpi=200)
    bars = ax.bar(monthly["month"], monthly["total_delay_days"], color="#1F4E79", width=0.55)
    ax.set_title("Monthly Total Delay Days (Jan - Mar)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Total Delay Days", fontsize=11)
    ax.tick_params(axis="both", labelsize=10)
    ax.set_ylim(0, monthly["total_delay_days"].max() * 1.18)
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for bar, val in zip(bars, monthly["total_delay_days"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, f"{val:g}",
                ha="center", va="bottom", fontsize=10, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def export_outputs(df, service, hub, route, monthly, out_dir: Path = OUT_DIR) -> dict[str, Path]:
    """Write all CSV outputs and the chart. Returns the generated paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "clean_data": out_dir / "clean_data.csv",
        "service": out_dir / "python_summary.csv",
        "hub": out_dir / "python_hub_summary.csv",
        "route": out_dir / "python_route_summary.csv",
        "monthly": out_dir / "python_monthly_summary.csv",
        "chart": out_dir / "python_chart.png",
    }
    clean_out = df.copy()
    clean_out["month"] = clean_out["month"].astype(str)
    clean_out["is_delayed"] = clean_out["is_delayed"].astype(int)
    clean_out = clean_out[["record_id", "month", "route_id", "route", "hub", "service_type",
                           "promised_days", "actual_days", "delay_days", "is_delayed"]]
    clean_out.to_csv(paths["clean_data"], index=False, encoding="utf-8")
    service.to_csv(paths["service"], index=False, encoding="utf-8", float_format="%.2f")
    hub.to_csv(paths["hub"], index=False, encoding="utf-8", float_format="%.2f")
    route.to_csv(paths["route"], index=False, encoding="utf-8", float_format="%.2f")
    monthly.to_csv(paths["monthly"], index=False, encoding="utf-8", float_format="%.2f")
    create_monthly_chart(monthly, paths["chart"])
    return paths


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    hash_before = {p.name: file_sha256(p) for p in (DELIVERIES_FILE, ROUTES_FILE)}

    deliveries, routes = load_data()
    facts = validate_raw_data(deliveries, routes)
    clean = clean_deliveries(deliveries)
    merged = merge_routes(clean, routes)
    df = calculate_metrics(merged)

    service = build_service_summary(df)
    hub = build_hub_summary(df)
    route = build_route_summary(df)
    monthly = build_monthly_summary(df)
    reconcile_summaries(df, service, hub, route, monthly)
    paths = export_outputs(df, service, hub, route, monthly)

    hash_after = {p.name: file_sha256(p) for p in (DELIVERIES_FILE, ROUTES_FILE)}
    if hash_before != hash_after:
        raise RuntimeError("Raw data files changed during analysis - this must never happen.")

    pd.set_option("display.width", 120)
    print("=== Delivery Delay Analysis ===")
    print(f"Raw delivery rows : {facts['raw_delivery_rows']}  (exact duplicates: {facts['exact_duplicate_rows']})")
    print(f"Clean delivery rows: {len(df)}   Route rows: {facts['route_rows']}")
    print("Raw files unchanged (SHA-256 verified).\n")
    print("Overall:", overall_metrics(df), "\n")
    print("Service-type summary\n", service.to_string(index=False), "\n")
    print("Hub summary\n", hub.to_string(index=False), "\n")
    print("Route summary\n", route.to_string(index=False), "\n")
    print("Monthly summary\n", monthly.to_string(index=False), "\n")
    print("Outputs written:")
    for p in paths.values():
        print("  -", p.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
