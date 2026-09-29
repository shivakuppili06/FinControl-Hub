"""Central config loading."""
import yaml
from pathlib import Path

with open(Path(__file__).parent / "config.yaml") as f:
    config = yaml.safe_load(f)

IPV_THRESHOLD_BPS = config["controls"]["ipv_threshold_bps"]
RECON_TOLERANCE = config["controls"]["recon_tolerance"]
PNL_PCT_THRESHOLD = config["controls"]["pnl_pct_threshold"]
PNL_ABS_THRESHOLD = config["controls"]["pnl_abs_threshold"]
LCR_MINIMUM = config["controls"]["lcr_minimum"]
INFLOW_CAP = config["controls"]["inflow_cap"]
DB_PATH = config["paths"]["db_path"]
