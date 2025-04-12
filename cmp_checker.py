#!/usr/bin/env python3
"""
system_monitor.py

A headless system monitor for macOS that:
  1. Checks system metrics (disk, memory, CPU load, network usage)
  2. Monitors top processes by CPU and memory
  3. Watches user-specified folders for size growth
  4. Logs alerts when thresholds are exceeded (with desktop notifications)
  5. Uses an external JSON configuration (if available)
  6. Rotates its own log file so logs don’t balloon out of control
  7. Appends historical data to a CSV for trend analysis
  8. Computes simple adaptive (baseline) averages over prior runs

Dependencies:
  pip install psutil humanize

Usage:
  python3 system_monitor.py

You can schedule it with launchd for periodic background monitoring.
"""

import os
import json
import time
import psutil
import shutil
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import csv
import humanize

print("✅ cmp_checker.py started")


# ======== 1. External Configuration ========
# Path to external configuration file
CONFIG_PATH = os.path.expanduser("~/sysmon_config.json")

# Default configuration values
default_config = {
    "DISK_THRESHOLD": 85,              # percent
    "RAM_THRESHOLD": 80,               # percent
    "LOAD_THRESHOLD": 6,               # 1-min CPU load average
    "DOWNLOADS_SIZE_THRESHOLD": 6 * 1024**3,  # 6 GB in bytes
    "CACHE_SIZE_THRESHOLD": 1 * 1024**3,      # 1 GB in bytes
    "NETWORK_THRESHOLD": 500 * 1024**2,  # 500 MB (example threshold increase)
    "FOLDERS": {
        "Downloads": "~/Downloads",
        "mapem": "~/Desktop/mapem"
    },
    "REFRESH_INTERVAL": 300,           # 5 minutes in seconds
    "CSV_LOG_PATH": "~/sysmon_metrics.csv",
    "BASELINE_COUNT": 5                # number of recent entries to compute a baseline
}

# Load configuration from file if exists; otherwise use defaults.
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}. Using defaults.")
        config = default_config
else:
    config = default_config

# Expand paths in the configuration
config["CSV_LOG_PATH"] = os.path.expanduser(config.get("CSV_LOG_PATH", "~/sysmon_metrics.csv"))
for key in config["FOLDERS"]:
    config["FOLDERS"][key] = os.path.expanduser(config["FOLDERS"][key])

# ======== 2. Setup Rotating Logging ========
LOG_FILE = os.path.expanduser("~/sysmon.log")
logger = logging.getLogger("sysmon")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024**2, backupCount=3)  # 5MB per file, 3 backups
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# ======== 3. Utility Functions ========
def human_readable(size_bytes):
    """Return a human-readable string for a file size."""
    return humanize.naturalsize(size_bytes, binary=True)

def folder_size(path):
    """Calculate total size of a folder in bytes."""
    total = 0
    for root, dirs, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            try:
                fp = os.path.join(root, f)
                total += os.path.getsize(fp)
            except Exception:
                continue
    return total

def get_top_processes(n=5):
    """Return two lists: top n processes sorted by CPU and by memory."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    top_cpu = sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)[:n]
    top_mem = sorted(procs, key=lambda x: x['memory_percent'], reverse=True)[:n]
    return top_cpu, top_mem

def send_notification(message, title="System Monitor Alert"):
    """Send a macOS desktop notification using AppleScript."""
    try:
        subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'],
                       check=True)
    except Exception as e:
        logger.error(f"Notification error: {e}")

def log_to_csv(metrics):
    """Append metrics dictionary to CSV log file."""
    csv_path = config["CSV_LOG_PATH"]
    file_exists = os.path.isfile(csv_path)
    fieldnames = list(metrics.keys())
    try:
        with open(csv_path, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(metrics)
    except Exception as e:
        logger.error(f"CSV Logging error: {e}")

def compute_baseline():
    """Compute the average for the last few entries from the CSV log.
       Returns a dict with baseline values, or None if not enough entries."""
    csv_path = config["CSV_LOG_PATH"]
    baseline_count = config.get("BASELINE_COUNT", 5)
    if not os.path.exists(csv_path):
        return None
    try:
        with open(csv_path, "r") as csvfile:
            reader = list(csv.DictReader(csvfile))
            if len(reader) < baseline_count:
                return None
            recent = reader[-baseline_count:]
            # Compute average for disk, mem, load, downloads_size, cache_size
            avg = {}
            for key in ["disk_percent", "mem_percent", "load_avg", "downloads_bytes", "cache_bytes"]:
                total = sum(float(row.get(key, 0)) for row in recent)
                avg[key] = total / len(recent)
            return avg
    except Exception as e:
        logger.error(f"Error computing baseline: {e}")
        return None

# ======== 4. Main Monitoring Function ========
def monitor_once():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # System metrics
    disk = psutil.disk_usage('/')
    mem = psutil.virtual_memory()
    try:
        load_avg = psutil.getloadavg()[0]  # 1-minute load average
    except Exception:
        load_avg = 0.0

    # Network metrics (cumulative since boot)
    net = psutil.net_io_counters()
    bytes_sent = net.bytes_sent
    bytes_recv = net.bytes_recv

    # Folder metrics: watch user-defined folders
    folder_metrics = {}
    for name, path in config["FOLDERS"].items():
        size = folder_size(path)
        folder_metrics[name + "_bytes"] = size

    # Build metrics record
    metrics = {
        "timestamp": timestamp,
        "disk_percent": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "mem_percent": mem.percent,
        "mem_used": mem.used,
        "mem_total": mem.total,
        "load_avg": load_avg,
        "bytes_sent": bytes_sent,
        "bytes_recv": bytes_recv,
    }
    metrics.update(folder_metrics)

    # Log current status
    logger.info(f"Metrics: {metrics}")
    log_to_csv(metrics)

    # ==== 4.a Check thresholds and send notifications ====
    issues = []
    if disk.percent >= config["DISK_THRESHOLD"]:
        issues.append(f"Disk usage high: {disk.percent:.1f}%")
    if mem.percent >= config["RAM_THRESHOLD"]:
        issues.append(f"Memory usage high: {mem.percent:.1f}%")
    if load_avg >= config["LOAD_THRESHOLD"]:
        issues.append(f"High CPU load: {load_avg:.2f}")
    for folder_name, path in config["FOLDERS"].items():
        threshold = config.get(f"{folder_name.upper()}_SIZE_THRESHOLD", None)
        # Use a key like "Downloads_size_threshold" if defined, else use default thresholds from config:
        if folder_name.lower() == "downloads":
            threshold = config.get("DOWNLOADS_SIZE_THRESHOLD", default_config["DOWNLOADS_SIZE_THRESHOLD"])
        elif folder_name.lower() == "mapem":
            threshold = config.get("CACHE_SIZE_THRESHOLD", default_config["CACHE_SIZE_THRESHOLD"])  # example: use cache threshold for mapem if desired
        size = folder_metrics.get(folder_name + "_bytes", 0)
        if threshold and size >= threshold:
            issues.append(f"{folder_name} folder size high: {human_readable(size)}")

    if issues:
        msg = "; ".join(issues)
        logger.warning(msg)
        send_notification(msg, "System Monitor Alert")

    # ==== 4.b Log top processes by CPU and memory if load is high ====
    if load_avg >= config["LOAD_THRESHOLD"]:
        top_cpu, top_mem = get_top_processes(5)
        proc_report = "Top CPU processes: " + ", ".join([f"{p['name']}({p['cpu_percent']}%)" for p in top_cpu])
        proc_report += "\nTop Memory processes: " + ", ".join([f"{p['name']}({p['memory_percent']}%)" for p in top_mem])
        logger.info(proc_report)
        # Optionally, send a notification with just one summary line (to avoid spamming)
        send_notification("High load detected. Check sysmon.log for process details.", "Process Alert")

    # ==== 4.c Adaptive Baseline Check ====
    baseline = compute_baseline()
    if baseline:
        # If any current metric is significantly above the baseline, log it
        adaptive_msgs = []
        for key, current in [("disk_percent", disk.percent),
                             ("mem_percent", mem.percent),
                             ("load_avg", load_avg)]:
            base_val = baseline.get(key, None)
            if base_val and current > base_val * 1.2:  # 20% above baseline
                adaptive_msgs.append(f"{key} is {current:.1f} vs baseline {base_val:.1f}")
        if adaptive_msgs:
            adaptive_msg = "Adaptive alert: " + "; ".join(adaptive_msgs)
            logger.info(adaptive_msg)
            send_notification(adaptive_msg, "Adaptive Threshold Alert")

# ======== 5. Main Execution =========
def main():
    # If you want this to run as a one-off invocation (e.g., via launchd), just call monitor_once().
    monitor_once()

if __name__ == "__main__":
    main()
