import os, functools, requests, pandas as pd, numpy as np
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
app = FastAPI(title="Wind Forecast Evaluator")

def stream(ds, params):
    r = requests.get(f"{BASE}/{ds}/stream", params=params, timeout=60)
    r.raise_for_status()
    return r.json()

@functools.lru_cache(maxsize=1)
def load():
    """Actuals (FUELHH, WIND) and forecasts (WINDFOR) for Jan 2026 targets."""
    act, fc = [], []
    d = datetime(2026, 1, 1)
    while d < datetime(2026, 2, 1):
        e = d + timedelta(days=7)
        act += stream("FUELHH", {"settlementDateFrom": d.date().isoformat(),
                                 "settlementDateTo": min(e, datetime(2026, 2, 1)).date().isoformat(),
                                 "fuelType": "WIND"})
        d = e
    d = datetime(2025, 12, 30)  # forecasts for 1 Jan are published the day before
    while d < datetime(2026, 2, 1):
        e = d + timedelta(days=2)
        fc += stream("WINDFOR", {"publishDateTimeFrom": d.isoformat() + "Z",
                                 "publishDateTimeTo": e.isoformat() + "Z"})
        d = e
    a = pd.DataFrame(act)[["startTime", "generation"]].rename(columns={"generation": "actual"})
    f = pd.DataFrame(fc)[["startTime", "publishTime", "generation"]].rename(columns={"generation": "forecast"})
    for df in (a, f):
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    f["publishTime"] = pd.to_datetime(f["publishTime"], utc=True)
    return a.drop_duplicates("startTime"), f

def decision_forecast(f, cutoff_hour):
    """For each target slot on day D, latest forecast published at/before (D-1) cutoff_hour:00 UTC.
    GB day-ahead gate closure is ~09:20 UK time; winter UK time == UTC."""
    f = f.copy()
    day = f["startTime"].dt.normalize()
    f["cutoff"] = day - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff_hour)
    f = f[(f["publishTime"] <= f["cutoff"]) & (day >= "2026-01-01") & (day < "2026-02-01")]
    f = f.sort_values("publishTime").groupby("startTime").tail(1)
    f["horizon_h"] = (f["startTime"] - f["publishTime"]).dt.total_seconds() / 3600
    return f

@app.get("/api/data")
def data(cutoff_hour: float = Query(9, ge=0, le=23)):
    a, f = load()
    m = decision_forecast(f, cutoff_hour).merge(a, on="startTime", how="inner").sort_values("startTime")
    m["error"] = m["forecast"] - m["actual"]
    e = m["error"]
    nz = m[m["actual"] > 0]
    metrics = {"n": len(m), "mae": e.abs().mean(), "rmse": float(np.sqrt((e ** 2).mean())),
               "bias": e.mean(), "p95_abs_error": e.abs().quantile(0.95),
               "mape_pct": (nz["error"].abs() / nz["actual"]).mean() * 100,
               "mean_actual": m["actual"].mean()}
    m["day"] = m["startTime"].dt.strftime("%Y-%m-%d")
    daily = m.groupby("day").agg(mae=("error", lambda x: x.abs().mean()), bias=("error", "mean")).reset_index()
    rows = m[["startTime", "publishTime", "horizon_h", "forecast", "actual", "error"]].copy()
    rows["startTime"] = rows["startTime"].astype(str); rows["publishTime"] = rows["publishTime"].astype(str)
    return {"metrics": metrics, "daily": daily.to_dict("records"), "rows": rows.to_dict("records")}

@app.get("/api/latest")
def latest():
    """Latest forecast per target slot (what a buyer sees right now)."""
    _, f = load()
    l = f.sort_values("publishTime").groupby("startTime").tail(1).sort_values("startTime")
    l = l.astype({"startTime": str, "publishTime": str})
    return l.to_dict("records")

if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True))
