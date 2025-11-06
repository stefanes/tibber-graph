"""Test to verify Y-axis tick values are calculated correctly."""
import sys
from pathlib import Path

# Add local_render directory to path
sys.path.insert(0, str(Path(__file__).parent / "local_render"))

from local_render import generate_price_data, aggregate_to_hourly
import datetime
from dateutil import tz

dates, prices, now = generate_price_data(fixed_time='19:34')
dates_agg, prices_agg = aggregate_to_hourly(dates, prices)

LOCAL_TZ = tz.tzlocal()
now_local = datetime.datetime.now(LOCAL_TZ).replace(hour=19, minute=34, second=0, microsecond=0)
now_hour_start = now_local.replace(minute=0, second=0, microsecond=0)

# Simulate the logic from renderer.py
visible_indices = list(range(len(dates_agg)))
candidate_indices = [i for i in visible_indices if dates_agg[i] >= now_hour_start]

# All visible prices (for Y-axis limits)
y_min_all = min(prices_agg)
y_max_all = max(prices_agg)

# Future prices only (for Y-axis ticks)
future_prices = [prices_agg[i] for i in candidate_indices]
y_min_tick = min(future_prices)
y_max_tick = max(future_prices)

print("Y-axis calculations:")
print("=" * 70)
print(f"All visible prices (for Y-axis limits):")
print(f"  Min: {y_min_all:.4f} ({y_min_all*100:.0f} öre)")
print(f"  Max: {y_max_all:.4f} ({y_max_all*100:.0f} öre)")
print()
print(f"Future prices only (for Y-axis ticks):")
print(f"  Min: {y_min_tick:.4f} ({y_min_tick*100:.0f} öre)")
print(f"  Max: {y_max_tick:.4f} ({y_max_tick*100:.0f} öre)")
print()
print("Expected behavior:")
print("  - Y-axis limits should span all visible data (61 to 215 öre)")
print("  - Y-axis max tick should show 183 öre (tomorrow 18:00)")
print("  - Y-axis should NOT show 187 öre (today 18:00 - in the past)")
