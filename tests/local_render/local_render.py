"""Local rendering script for Tibber graph with sample data.

Usage:
    python local_render.py               # Use defaults.py + config.py with test overrides from tests/local_render/config.py
    python local_render.py --no-override # Use only component defaults.py + config.py (ignore test overrides)

This will generate a rendered graph image 'local_render.png' in the current directory.
"""
import datetime
import sys
from pathlib import Path

# Check for command-line arguments
use_overrides = True
if len(sys.argv) > 1:
    if sys.argv[1] in ('--no-override', '--no-overrides', '-n'):
        use_overrides = False
        print("Running with component configuration only (test overrides disabled)")
    elif sys.argv[1] in ('--help', '-h'):
        print(__doc__)
        sys.exit(0)

# Load the constants and rendering code without importing the package
# This avoids Home Assistant dependencies
component_dir = Path(__file__).parent.parent.parent / "custom_components" / "tibber_graph"

# Read and execute defaults.py to load all default constants
defaults_file = component_dir / "defaults.py"
with open(defaults_file, 'r', encoding='utf-8') as f:
    defaults_code = f.read()
    exec(defaults_code, globals())

# Read and execute config.py to load user configuration (overrides defaults.py)
config_file = component_dir / "config.py"
with open(config_file, 'r', encoding='utf-8') as f:
    config_code = f.read()
    # Replace relative import since we've already loaded defaults
    config_code = config_code.replace('from .defaults import *', '')
    exec(config_code, globals())

# Load test-specific configuration overrides (unless disabled)
if use_overrides:
    test_config_file = Path(__file__).parent / "config.py"
    with open(test_config_file, 'r', encoding='utf-8') as f:
        test_config_code = f.read()
        exec(test_config_code, globals())
    print("Using test configuration from tests/local_render/config.py")
else:
    print("Using component configuration only (defaults.py + config.py)")

# Read and execute renderer.py (replacing relative import)
renderer_file = component_dir / "renderer.py"
with open(renderer_file, 'r', encoding='utf-8') as f:
    renderer_code = f.read()
    # Replace relative import with already loaded constants
    renderer_code = renderer_code.replace('from .config import *', '')
    exec(renderer_code, globals())

# Import just the _aggregate_to_hourly function from camera.py
# We extract and execute only the static method to avoid Home Assistant dependencies
# This ensures the test code uses the exact same aggregation logic as the real component
camera_file = component_dir / "camera.py"
with open(camera_file, 'r', encoding='utf-8') as f:
    camera_lines = f.readlines()
    # Find and extract the _aggregate_to_hourly method
    in_method = False
    method_lines = []
    for i, line in enumerate(camera_lines):
        if 'def _aggregate_to_hourly(' in line:
            in_method = True
            # Remove @staticmethod decorator and adjust indentation
            method_lines.append(line.replace('    def _aggregate_to_hourly', 'def aggregate_to_hourly'))
        elif in_method:
            # Check if we've reached the next method or class-level code
            if line.strip() and not line.startswith(' ' * 8) and not line.startswith(' ' * 4 + '@'):
                break
            # Add line with reduced indentation (remove 4 spaces)
            if line.startswith('        '):
                method_lines.append(line[4:])
            elif line.strip():
                method_lines.append(line)
            else:
                method_lines.append(line)

    aggregate_code = ''.join(method_lines)
    exec(aggregate_code, globals())

from dateutil import tz

# Configuration
OUTPUT_FILE = "local_render.png"
# Width, height, and currency are loaded from const.py:
# - CANVAS_WIDTH and CANVAS_HEIGHT
# - CURRENCY_OVERRIDE

# Local timezone
LOCAL_TZ = tz.tzlocal()


def generate_price_data():
    """Generate sample price data for testing."""
    # Current time
    now = datetime.datetime.now(LOCAL_TZ)

    # Generate 48 hours of data (today from midnight + tomorrow) in 15-minute intervals
    # Start at midnight today
    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

    dates = []
    prices = []

    # Create 15-minute interval price data with some variation
    base_price = 0.45  # Base price in currency units (e.g., NOK/kWh)

    # 48 hours * 4 intervals per hour = 192 data points
    for i in range(48 * 4):
        interval_time = start_time + datetime.timedelta(minutes=i * 15)
        dates.append(interval_time)

        # Create a pattern: cheaper at night, more expensive during day
        hour = interval_time.hour

        # Night discount (00:00-06:00)
        if 0 <= hour < 6:
            price = base_price * 0.6
        # Morning rise (06:00-09:00)
        elif 6 <= hour < 9:
            price = base_price * 0.9
        # Peak hours (09:00-17:00)
        elif 9 <= hour < 17:
            price = base_price * 1.3
        # Evening (17:00-21:00)
        elif 17 <= hour < 21:
            price = base_price * 1.5
        # Night (21:00-00:00)
        else:
            price = base_price * 0.8

        # Add some random variation (±10%)
        import random
        price *= random.uniform(0.9, 1.1)

        prices.append(price)

    return dates, prices, now


def main():
    """Generate test render."""
    print("Generating sample price data...")
    dates_raw, prices_raw, now_local = generate_price_data()

    # Aggregate to hourly prices if configured (using camera.py's method)
    if USE_HOURLY_PRICES:
        print("Aggregating 15-minute data to hourly averages...")
        dates_raw, prices_raw = aggregate_to_hourly(dates_raw, prices_raw)

    # Find current price index
    idx = 0
    for i, date in enumerate(dates_raw):
        if date <= now_local:
            idx = i
        else:
            break

    # Determine step size based on actual data interval
    if len(dates_raw) >= 2:
        step_minutes = int((dates_raw[1] - dates_raw[0]).total_seconds() // 60) or (60 if USE_HOURLY_PRICES else 15)
    else:
        step_minutes = 60 if USE_HOURLY_PRICES else 15

    interval_td = datetime.timedelta(minutes=step_minutes)
    dates_plot = dates_raw + [dates_raw[-1] + interval_td]
    prices_plot = prices_raw + [prices_raw[-1]]

    print(f"Data range: {dates_raw[0].strftime('%Y-%m-%d %H:%M')} to {dates_raw[-1].strftime('%Y-%m-%d %H:%M')}")
    print(f"Current time: {now_local.strftime('%Y-%m-%d %H:%M')}")
    print(f"Data points: {len(dates_raw)} ({'hourly' if USE_HOURLY_PRICES else '15-minute'} intervals)")
    print(f"Current price index: {idx}")
    print(f"Price range: {min(prices_raw):.4f} - {max(prices_raw):.4f}")
    print(f"Current price: {prices_raw[idx]:.4f}")

    # Use currency from configuration (CURRENCY_OVERRIDE or default to SEK)
    currency = CURRENCY_OVERRIDE if CURRENCY_OVERRIDE else "SEK"

    print(f"\nRendering to {OUTPUT_FILE}...")
    print(f"Active configuration:")
    print(f"  - Canvas size: {CANVAS_WIDTH}x{CANVAS_HEIGHT}")
    print(f"  - Currency: {currency}")
    render_plot_to_path(
        width=CANVAS_WIDTH,
        height=CANVAS_HEIGHT,
        dates_plot=dates_plot,
        prices_plot=prices_plot,
        dates_raw=dates_raw,
        prices_raw=prices_raw,
        now_local=now_local,
        idx=idx,
        currency=currency,
        out_path=OUTPUT_FILE,
    )

    print(f"✓ Successfully rendered to {OUTPUT_FILE}")
    print("\nYou can now open the image to see the result!")


if __name__ == "__main__":
    main()
