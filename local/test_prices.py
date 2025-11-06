"""Quick test to check the prices around hour 19."""
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

print('All hourly prices (showing all data):')
print('-' * 70)
for i, (d, p) in enumerate(zip(dates_agg, prices_agg)):
    future_marker = " <-- FUTURE" if d >= now_hour_start else " <-- PAST"
    print(f'Index {i:2d}: {d.strftime("%Y-%m-%d %H:%M")} - {p:.4f} ({p*100:.0f} öre){future_marker}')

# Find max in future values
future_indices = [i for i, d in enumerate(dates_agg) if d >= now_hour_start]
if future_indices:
    max_future_idx = max(future_indices, key=lambda i: prices_agg[i])
    print(f'\n{"="*70}')
    print(f'Max future price should be at index {max_future_idx}:')
    print(f'  {dates_agg[max_future_idx].strftime("%Y-%m-%d %H:%M")} - {prices_agg[max_future_idx]:.4f} ({prices_agg[max_future_idx]*100:.0f} öre)')
    print(f'{"="*70}')

print('\nAt time 19:34:')
print(f'  Current hour start: {now_hour_start.strftime("%Y-%m-%d %H:%M")}')
print(f'  Should include hour 19 and later as "future" values')
