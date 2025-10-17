"""Local rendering script for Tibber graph with sample data.

Usage:
    python local_render.py                 # Use defaults.py + tests/local_render/config.py (test configuration)
    python local_render.py --no-override   # Use defaults.py + component config.py (production configuration)
    python local_render.py --defaults-only # Use only defaults.py (pure defaults, no overrides)
    python local_render.py --random        # Use random generated price data instead of real Tibber data
    python local_render.py --time 19:34    # Simulate a specific time (e.g., 19:34 today)

This will generate a rendered graph image 'local_render.png' in the current directory.
"""
import datetime
import sys
from pathlib import Path

# Check for command-line arguments
config_mode = 'test'  # 'test', 'component', or 'defaults'
use_random_data = False
fixed_time = None

i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg in ('--no-override', '--no-overrides', '-n'):
        config_mode = 'component'
        print("Running with component configuration (defaults.py + config.py)")
    elif arg in ('--defaults-only', '--defaults', '-d'):
        config_mode = 'defaults'
        print("Running with defaults only (no configuration overrides)")
    elif arg in ('--random', '-r'):
        use_random_data = True
        print("Using randomly generated price data")
    elif arg in ('--time', '-t'):
        if i + 1 < len(sys.argv):
            fixed_time = sys.argv[i + 1]
            print(f"Simulating time: {fixed_time}")
            i += 1  # Skip next argument
        else:
            print("Error: --time requires a time argument (e.g., --time 19:34)")
            sys.exit(1)
    elif arg in ('--help', '-h'):
        print(__doc__)
        sys.exit(0)
    else:
        print(f"Unknown argument: {arg}")
        print("Use --help for usage information")
        sys.exit(1)
    i += 1

# Load the constants and rendering code without importing the package
# This avoids Home Assistant dependencies
component_dir = Path(__file__).parent.parent.parent / "custom_components" / "tibber_graph"

# Read and execute defaults.py to load all default constants
defaults_file = component_dir / "defaults.py"
with open(defaults_file, 'r', encoding='utf-8') as f:
    defaults_code = f.read()
    exec(defaults_code, globals())

# Load configuration based on mode
if config_mode == 'test':
    # Load test-specific configuration overrides (if it exists)
    # Note: We skip the component's config.py and only use the test config.py
    test_config_file = Path(__file__).parent / "config.py"
    if test_config_file.exists():
        with open(test_config_file, 'r', encoding='utf-8') as f:
            test_config_code = f.read()
            exec(test_config_code, globals())
        print("Using test configuration from tests/local_render/config.py")
    else:
        print("Using only defaults.py (test config.py not found)")
elif config_mode == 'component':
    # Use the component's config.py (if it exists)
    config_file = component_dir / "config.py"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config_code = f.read()
            # Replace relative import since we've already loaded defaults
            config_code = config_code.replace('from .defaults import *', '')
            exec(config_code, globals())
        print("Using component configuration from config.py")
    else:
        print("Using only defaults.py (config.py not found)")
elif config_mode == 'defaults':
    # Use only defaults, no config overrides
    print("Using only defaults.py (no configuration overrides)")

# Read and execute renderer.py (replacing relative import)
renderer_file = component_dir / "renderer.py"
with open(renderer_file, 'r', encoding='utf-8') as f:
    renderer_code = f.read()
    # Replace the try-except import block with nothing (constants already loaded)
    import re
    # Remove the entire try-except import block
    renderer_code = re.sub(
        r'# Import configuration.*?\n(?:try:.*?except.*?:.*?\n(?:    .*?\n)*)',
        '',
        renderer_code,
        flags=re.DOTALL
    )
    # Also handle old-style import if present
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


def generate_price_data(use_random=False, fixed_time=None):
    """Generate sample price data for testing.

    Args:
        use_random: If True, generate random price data instead of using real Tibber data
        fixed_time: Optional time string in format "HH:MM" to simulate a specific time (e.g., "19:34")
    """
    # Current time (or override with fixed time)
    now = datetime.datetime.now(LOCAL_TZ)
    if fixed_time:
        # Parse fixed_time as "HH:MM" and set it to today
        time_parts = fixed_time.split(':')
        if len(time_parts) == 2:
            hour, minute = int(time_parts[0]), int(time_parts[1])
            now = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Get today's and tomorrow's dates for dynamic date generation
    today = now.date()
    tomorrow = today + datetime.timedelta(days=1)
    today_str = today.strftime('%Y-%m-%d')
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')

    if use_random:
        # Generate random price data following real Tibber price patterns
        # Analysis of real data shows:
        # - Night (00:00-04:00): Low prices ~0.60-0.82
        # - Early morning rise (04:00-06:00): Sharp increase ~0.70-1.43
        # - Morning peak (06:00-09:00): Highest prices ~1.27-2.37
        # - Day volatility (09:00-15:00): High fluctuation ~1.17-2.37
        # - Afternoon (15:00-17:00): Moderate ~1.18-1.71
        # - Evening peak (17:00-19:00): Second peak ~1.34-2.22
        # - Evening decline (19:00-23:00): Gradual decrease ~1.58-0.86

        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        dates = []
        prices = []

        import random

        # 48 hours * 4 intervals per hour = 192 data points
        for i in range(48 * 4):
            interval_time = start_time + datetime.timedelta(minutes=i * 15)
            dates.append(interval_time)

            # Determine which day we're in (first or second)
            hour = interval_time.hour
            day_offset = 1 if interval_time.date() > today else 0

            # Base price patterns by hour (mimicking real Tibber data)
            if 0 <= hour < 4:
                # Night: Low and stable
                base_price = random.uniform(0.60, 0.82)
                variation = random.uniform(-0.02, 0.02)
            elif 4 <= hour < 6:
                # Early morning: Sharp rise
                # Interpolate between 0.70 and 1.43 based on position in range
                progress = (hour - 4) / 2.0 + (interval_time.minute / 60.0) / 2.0
                base_price = 0.70 + (1.43 - 0.70) * progress
                variation = random.uniform(-0.15, 0.20)
            elif 6 <= hour < 9:
                # Morning peak: Highest prices with high volatility
                base_price = random.uniform(1.50, 2.30)
                # Add spikes
                if random.random() < 0.3:
                    base_price += random.uniform(0.1, 0.4)
                variation = random.uniform(-0.20, 0.25)
            elif 9 <= hour < 15:
                # Day: High prices with volatility
                base_price = random.uniform(1.20, 1.90)
                # Occasional spikes
                if random.random() < 0.2:
                    base_price += random.uniform(0.2, 0.5)
                variation = random.uniform(-0.15, 0.20)
            elif 15 <= hour < 17:
                # Afternoon: Moderate to high
                base_price = random.uniform(1.15, 1.50)
                variation = random.uniform(-0.10, 0.25)
            elif 17 <= hour < 19:
                # Evening peak: Second highest period
                base_price = random.uniform(1.50, 2.00)
                # Add spikes
                if random.random() < 0.25:
                    base_price += random.uniform(0.1, 0.3)
                variation = random.uniform(-0.20, 0.30)
            elif 19 <= hour < 21:
                # Early evening: Declining
                progress = (hour - 19) / 2.0 + (interval_time.minute / 60.0) / 2.0
                base_price = 1.40 - (1.40 - 1.00) * progress
                variation = random.uniform(-0.15, 0.15)
            else:  # 21 <= hour < 24
                # Late evening: Lower prices
                base_price = random.uniform(0.85, 1.05)
                variation = random.uniform(-0.10, 0.10)

            # Second day tends to have slightly different prices
            if day_offset == 1:
                # Adjust second day to be slightly lower on average
                base_price *= random.uniform(0.85, 0.95)

            price = max(0.50, base_price + variation)  # Ensure price doesn't go too low
            prices.append(price)

        return dates, prices, now

    # Real price data from Tibber (with dynamic dates)
    price_data = [
        (f'{today_str}T00:00:00.000+02:00', 0.6123),
        (f'{today_str}T00:15:00.000+02:00', 0.6096),
        (f'{today_str}T00:30:00.000+02:00', 0.6079),
        (f'{today_str}T00:45:00.000+02:00', 0.6061),
        (f'{today_str}T01:00:00.000+02:00', 0.6046),
        (f'{today_str}T01:15:00.000+02:00', 0.6056),
        (f'{today_str}T01:30:00.000+02:00', 0.606),
        (f'{today_str}T01:45:00.000+02:00', 0.6076),
        (f'{today_str}T02:00:00.000+02:00', 0.6042),
        (f'{today_str}T02:15:00.000+02:00', 0.6052),
        (f'{today_str}T02:30:00.000+02:00', 0.6068),
        (f'{today_str}T02:45:00.000+02:00', 0.6078),
        (f'{today_str}T03:00:00.000+02:00', 0.6093),
        (f'{today_str}T03:15:00.000+02:00', 0.6108),
        (f'{today_str}T03:30:00.000+02:00', 0.6257),
        (f'{today_str}T03:45:00.000+02:00', 0.6508),
        (f'{today_str}T04:00:00.000+02:00', 0.6206),
        (f'{today_str}T04:15:00.000+02:00', 0.6418),
        (f'{today_str}T04:30:00.000+02:00', 0.6805),
        (f'{today_str}T04:45:00.000+02:00', 0.7073),
        (f'{today_str}T05:00:00.000+02:00', 0.7555),
        (f'{today_str}T05:15:00.000+02:00', 0.8929),
        (f'{today_str}T05:30:00.000+02:00', 1.1367),
        (f'{today_str}T05:45:00.000+02:00', 1.4263),
        (f'{today_str}T06:00:00.000+02:00', 1.2671),
        (f'{today_str}T06:15:00.000+02:00', 1.3758),
        (f'{today_str}T06:30:00.000+02:00', 1.7698),
        (f'{today_str}T06:45:00.000+02:00', 1.9536),
        (f'{today_str}T07:00:00.000+02:00', 1.7846),
        (f'{today_str}T07:15:00.000+02:00', 1.7673),
        (f'{today_str}T07:30:00.000+02:00', 1.9953),
        (f'{today_str}T07:45:00.000+02:00', 2.203),
        (f'{today_str}T08:00:00.000+02:00', 2.3625),
        (f'{today_str}T08:15:00.000+02:00', 2.3731),
        (f'{today_str}T08:30:00.000+02:00', 2.098),
        (f'{today_str}T08:45:00.000+02:00', 1.7845),
        (f'{today_str}T09:00:00.000+02:00', 2.3673),
        (f'{today_str}T09:15:00.000+02:00', 1.9702),
        (f'{today_str}T09:30:00.000+02:00', 1.7806),
        (f'{today_str}T09:45:00.000+02:00', 1.5144),
        (f'{today_str}T10:00:00.000+02:00', 1.8632),
        (f'{today_str}T10:15:00.000+02:00', 1.753),
        (f'{today_str}T10:30:00.000+02:00', 1.6036),
        (f'{today_str}T10:45:00.000+02:00', 1.479),
        (f'{today_str}T11:00:00.000+02:00', 1.6384),
        (f'{today_str}T11:15:00.000+02:00', 1.4837),
        (f'{today_str}T11:30:00.000+02:00', 1.3256),
        (f'{today_str}T11:45:00.000+02:00', 1.2328),
        (f'{today_str}T12:00:00.000+02:00', 1.4084),
        (f'{today_str}T12:15:00.000+02:00', 1.273),
        (f'{today_str}T12:30:00.000+02:00', 1.2569),
        (f'{today_str}T12:45:00.000+02:00', 1.22),
        (f'{today_str}T13:00:00.000+02:00', 1.338),
        (f'{today_str}T13:15:00.000+02:00', 1.2969),
        (f'{today_str}T13:30:00.000+02:00', 1.2657),
        (f'{today_str}T13:45:00.000+02:00', 1.2403),
        (f'{today_str}T14:00:00.000+02:00', 1.2528),
        (f'{today_str}T14:15:00.000+02:00', 1.3047),
        (f'{today_str}T14:30:00.000+02:00', 1.3416),
        (f'{today_str}T14:45:00.000+02:00', 1.3727),
        (f'{today_str}T15:00:00.000+02:00', 1.1758),
        (f'{today_str}T15:15:00.000+02:00', 1.2655),
        (f'{today_str}T15:30:00.000+02:00', 1.3526),
        (f'{today_str}T15:45:00.000+02:00', 1.3898),
        (f'{today_str}T16:00:00.000+02:00', 1.2462),
        (f'{today_str}T16:15:00.000+02:00', 1.3136),
        (f'{today_str}T16:30:00.000+02:00', 1.4096),
        (f'{today_str}T16:45:00.000+02:00', 1.7136),
        (f'{today_str}T17:00:00.000+02:00', 1.335),
        (f'{today_str}T17:15:00.000+02:00', 1.619),
        (f'{today_str}T17:30:00.000+02:00', 1.8213),
        (f'{today_str}T17:45:00.000+02:00', 2.2175),
        (f'{today_str}T18:00:00.000+02:00', 1.8756),
        (f'{today_str}T18:15:00.000+02:00', 1.9174),
        (f'{today_str}T18:30:00.000+02:00', 1.779),
        (f'{today_str}T18:45:00.000+02:00', 1.9252),
        (f'{today_str}T19:00:00.000+02:00', 1.5761),
        (f'{today_str}T19:15:00.000+02:00', 1.2993),
        (f'{today_str}T19:30:00.000+02:00', 1.2251),
        (f'{today_str}T19:45:00.000+02:00', 1.1769),
        (f'{today_str}T20:00:00.000+02:00', 1.1889),
        (f'{today_str}T20:15:00.000+02:00', 0.9576),
        (f'{today_str}T20:30:00.000+02:00', 0.9302),
        (f'{today_str}T20:45:00.000+02:00', 0.8955),
        (f'{today_str}T21:00:00.000+02:00', 0.9947),
        (f'{today_str}T21:15:00.000+02:00', 0.9871),
        (f'{today_str}T21:30:00.000+02:00', 0.969),
        (f'{today_str}T21:45:00.000+02:00', 0.9257),
        (f'{today_str}T22:00:00.000+02:00', 1.0201),
        (f'{today_str}T22:15:00.000+02:00', 1.0002),
        (f'{today_str}T22:30:00.000+02:00', 0.9448),
        (f'{today_str}T22:45:00.000+02:00', 0.9108),
        (f'{today_str}T23:00:00.000+02:00', 1.0119),
        (f'{today_str}T23:15:00.000+02:00', 0.9057),
        (f'{today_str}T23:30:00.000+02:00', 0.8841),
        (f'{today_str}T23:45:00.000+02:00', 0.8611),
        (f'{tomorrow_str}T00:00:00.000+02:00', 1.0343),
        (f'{tomorrow_str}T00:15:00.000+02:00', 0.9033),
        (f'{tomorrow_str}T00:30:00.000+02:00', 0.8518),
        (f'{tomorrow_str}T00:45:00.000+02:00', 0.8291),
        (f'{tomorrow_str}T01:00:00.000+02:00', 0.9154),
        (f'{tomorrow_str}T01:15:00.000+02:00', 0.8684),
        (f'{tomorrow_str}T01:30:00.000+02:00', 0.8323),
        (f'{tomorrow_str}T01:45:00.000+02:00', 0.8043),
        (f'{tomorrow_str}T02:00:00.000+02:00', 0.8526),
        (f'{tomorrow_str}T02:15:00.000+02:00', 0.8149),
        (f'{tomorrow_str}T02:30:00.000+02:00', 0.8052),
        (f'{tomorrow_str}T02:45:00.000+02:00', 0.7996),
        (f'{tomorrow_str}T03:00:00.000+02:00', 0.8032),
        (f'{tomorrow_str}T03:15:00.000+02:00', 0.7872),
        (f'{tomorrow_str}T03:30:00.000+02:00', 0.7611),
        (f'{tomorrow_str}T03:45:00.000+02:00', 0.7332),
        (f'{tomorrow_str}T04:00:00.000+02:00', 0.7478),
        (f'{tomorrow_str}T04:15:00.000+02:00', 0.73),
        (f'{tomorrow_str}T04:30:00.000+02:00', 0.7311),
        (f'{tomorrow_str}T04:45:00.000+02:00', 0.7289),
        (f'{tomorrow_str}T05:00:00.000+02:00', 0.7083),
        (f'{tomorrow_str}T05:15:00.000+02:00', 0.7132),
        (f'{tomorrow_str}T05:30:00.000+02:00', 0.722),
        (f'{tomorrow_str}T05:45:00.000+02:00', 0.7282),
        (f'{tomorrow_str}T06:00:00.000+02:00', 0.7615),
        (f'{tomorrow_str}T06:15:00.000+02:00', 0.7829),
        (f'{tomorrow_str}T06:30:00.000+02:00', 0.7873),
        (f'{tomorrow_str}T06:45:00.000+02:00', 0.7916),
        (f'{tomorrow_str}T07:00:00.000+02:00', 0.7833),
        (f'{tomorrow_str}T07:15:00.000+02:00', 0.7972),
        (f'{tomorrow_str}T07:30:00.000+02:00', 0.8002),
        (f'{tomorrow_str}T07:45:00.000+02:00', 0.8421),
        (f'{tomorrow_str}T08:00:00.000+02:00', 0.965),
        (f'{tomorrow_str}T08:15:00.000+02:00', 1.3929),
        (f'{tomorrow_str}T08:30:00.000+02:00', 1.5154),
        (f'{tomorrow_str}T08:45:00.000+02:00', 1.4094),
        (f'{tomorrow_str}T09:00:00.000+02:00', 1.1485),
        (f'{tomorrow_str}T09:15:00.000+02:00', 1.3214),
        (f'{tomorrow_str}T09:30:00.000+02:00', 1.338),
        (f'{tomorrow_str}T09:45:00.000+02:00', 1.0383),
        (f'{tomorrow_str}T10:00:00.000+02:00', 0.8435),
        (f'{tomorrow_str}T10:15:00.000+02:00', 0.8061),
        (f'{tomorrow_str}T10:30:00.000+02:00', 0.7938),
        (f'{tomorrow_str}T10:45:00.000+02:00', 0.7449),
        (f'{tomorrow_str}T11:00:00.000+02:00', 0.793),
        (f'{tomorrow_str}T11:15:00.000+02:00', 0.7873),
        (f'{tomorrow_str}T11:30:00.000+02:00', 0.78),
        (f'{tomorrow_str}T11:45:00.000+02:00', 0.7185),
        (f'{tomorrow_str}T12:00:00.000+02:00', 0.7354),
        (f'{tomorrow_str}T12:15:00.000+02:00', 0.723),
        (f'{tomorrow_str}T12:30:00.000+02:00', 0.6724),
        (f'{tomorrow_str}T12:45:00.000+02:00', 0.6451),
        (f'{tomorrow_str}T13:00:00.000+02:00', 0.6623),
        (f'{tomorrow_str}T13:15:00.000+02:00', 0.6499),
        (f'{tomorrow_str}T13:30:00.000+02:00', 0.6405),
        (f'{tomorrow_str}T13:45:00.000+02:00', 0.6361),
        (f'{tomorrow_str}T14:00:00.000+02:00', 0.64),
        (f'{tomorrow_str}T14:15:00.000+02:00', 0.6531),
        (f'{tomorrow_str}T14:30:00.000+02:00', 0.672),
        (f'{tomorrow_str}T14:45:00.000+02:00', 0.701),
        (f'{tomorrow_str}T15:00:00.000+02:00', 0.6684),
        (f'{tomorrow_str}T15:15:00.000+02:00', 0.7252),
        (f'{tomorrow_str}T15:30:00.000+02:00', 0.738),
        (f'{tomorrow_str}T15:45:00.000+02:00', 0.8547),
        (f'{tomorrow_str}T16:00:00.000+02:00', 0.898),
        (f'{tomorrow_str}T16:15:00.000+02:00', 1.227),
        (f'{tomorrow_str}T16:30:00.000+02:00', 1.5186),
        (f'{tomorrow_str}T16:45:00.000+02:00', 1.7864),
        (f'{tomorrow_str}T17:00:00.000+02:00', 1.2624),
        (f'{tomorrow_str}T17:15:00.000+02:00', 1.583),
        (f'{tomorrow_str}T17:30:00.000+02:00', 1.7358),
        (f'{tomorrow_str}T17:45:00.000+02:00', 1.9612),
        (f'{tomorrow_str}T18:00:00.000+02:00', 1.7895),
        (f'{tomorrow_str}T18:15:00.000+02:00', 1.8683),
        (f'{tomorrow_str}T18:30:00.000+02:00', 1.8751),
        (f'{tomorrow_str}T18:45:00.000+02:00', 1.7878),
        (f'{tomorrow_str}T19:00:00.000+02:00', 1.9269),
        (f'{tomorrow_str}T19:15:00.000+02:00', 1.7406),
        (f'{tomorrow_str}T19:30:00.000+02:00', 1.5726),
        (f'{tomorrow_str}T19:45:00.000+02:00', 1.4854),
        (f'{tomorrow_str}T20:00:00.000+02:00', 1.8791),
        (f'{tomorrow_str}T20:15:00.000+02:00', 1.5474),
        (f'{tomorrow_str}T20:30:00.000+02:00', 1.4386),
        (f'{tomorrow_str}T20:45:00.000+02:00', 1.3744),
        (f'{tomorrow_str}T21:00:00.000+02:00', 1.393),
        (f'{tomorrow_str}T21:15:00.000+02:00', 1.378),
        (f'{tomorrow_str}T21:30:00.000+02:00', 1.2872),
        (f'{tomorrow_str}T21:45:00.000+02:00', 1.2517),
        (f'{tomorrow_str}T22:00:00.000+02:00', 1.2678),
        (f'{tomorrow_str}T22:15:00.000+02:00', 1.2502),
        (f'{tomorrow_str}T22:30:00.000+02:00', 1.2268),
        (f'{tomorrow_str}T22:45:00.000+02:00', 1.2065),
        (f'{tomorrow_str}T23:00:00.000+02:00', 1.1369),
        (f'{tomorrow_str}T23:15:00.000+02:00', 1.1232),
        (f'{tomorrow_str}T23:30:00.000+02:00', 1.1122),
        (f'{tomorrow_str}T23:45:00.000+02:00', 1.0914),
    ]

    dates = []
    prices = []

    from dateutil import parser
    for time_str, price in price_data:
        dt = parser.isoparse(time_str)
        # Convert to local timezone
        dt_local = dt.astimezone(LOCAL_TZ)
        dates.append(dt_local)
        prices.append(price)

    return dates, prices, now


def main():
    """Generate test render."""
    print("Generating sample price data...")
    dates_raw, prices_raw, now_local = generate_price_data(
        use_random=use_random_data,
        fixed_time=fixed_time
    )

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
