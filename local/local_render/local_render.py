"""Local rendering script for Tibber graph with sample data.

Usage:
    python local_render.py                    # Use test configuration (light theme, colored labels)
    python local_render.py --wearos           # Use Wear OS configuration (dark theme, hourly, öre)
    python local_render.py --defaults         # Use only defaults.py (pure defaults, no overrides)
    python local_render.py --old-defaults     # Use old default values (before recent changes)
    python local_render.py --random           # Use random generated price data instead of real Tibber data
    python local_render.py --time 19:34       # Simulate a specific time (e.g., 19:34 today)
    python local_render.py --publish          # Publish mode: resize to 590px, add border/rounded corners, black bg if transparent
    python local_render.py --custom-theme '{"axis_label_color": "#d8b9ff", ...}'  # Use custom theme from JSON string

This will generate a rendered graph image at 'local/local_render.png'.
"""
import datetime
import json
import sys
from pathlib import Path

# Add parent directory to path to import test_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_helpers import load_price_data_from_json, parse_time_string

# Check for command-line arguments
config_mode = 'test'  # 'test', 'wearos', 'defaults', or 'old_defaults'
use_random_data = False
fixed_time = None
publish_mode = False  # Combines resize, border/corners, and black background for transparent images
custom_theme_json = None  # Custom theme config as JSON string

i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg in ('--wearos', '-w'):
        config_mode = 'wearos'
        print("Running with Wear OS configuration (inline settings)")
    elif arg in ('--defaults', '-d'):
        config_mode = 'defaults'
        print("Running with defaults only (no configuration overrides)")
    elif arg in ('--old-defaults', '-o'):
        config_mode = 'old_defaults'
        print("Running with old default values (before recent changes)")
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
    elif arg in ('--publish', '-p'):
        publish_mode = True
        print("Publish mode: will resize, add border/rounded corners, and convert transparent to black")
    elif arg in ('--custom-theme', '-c'):
        if i + 1 < len(sys.argv):
            custom_theme_json = sys.argv[i + 1]
            print(f"Using custom theme configuration")
            i += 1  # Skip next argument
        else:
            print("Error: --custom-theme requires a JSON string argument")
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

# Read and execute const.py to get DEFAULT_* constants (skipping imports)
const_file = component_dir / "const.py"
with open(const_file, 'r', encoding='utf-8') as f:
    const_code = f.read()
    # Remove the import section and domain definition
    import re
    # Remove everything up to "# Default values imported from defaults.py"
    const_code = re.sub(
        r'^.*?# Default values imported from defaults\.py',
        '# Default values imported from defaults.py',
        const_code,
        flags=re.DOTALL | re.MULTILINE
    )
    # Remove the DOMAIN line and config entry keys section (everything before DEFAULT_*)
    const_code = re.sub(
        r'DOMAIN = .*?\n\n.*?(?=# Default values)',
        '',
        const_code,
        flags=re.DOTALL
    )
    exec(const_code, globals())

# No additional loading needed - all modes use defaults.py as base
# Test modes will apply render_options inline in main()

# Load ensure_timezone function from helpers.py (without importing Home Assistant dependencies)
# Define it directly to avoid import issues
from dateutil import tz

# Reuse local timezone object
LOCAL_TZ = tz.tzlocal()

def ensure_timezone(dt, tz_info=None):
    """Ensure a datetime object has timezone information.

    Args:
        dt: datetime object to check
        tz_info: timezone to apply if missing (defaults to LOCAL_TZ)

    Returns:
        datetime object with timezone information
    """
    if tz_info is None:
        tz_info = LOCAL_TZ
    # For Python 3.11+, use replace() for all timezone objects
    return dt if dt.tzinfo else dt.replace(tzinfo=tz_info)

# Read and execute renderer.py (replacing relative imports)
renderer_file = component_dir / "renderer.py"
with open(renderer_file, 'r', encoding='utf-8') as f:
    renderer_code = f.read()
    # Replace the relative imports with nothing (constants already loaded)
    # Remove the entire import section from const and defaults
    renderer_code = re.sub(
        r'^# Import default constants from const\.py.*?\n\)',
        '# Constants already loaded from defaults.py and const.py',
        renderer_code,
        flags=re.DOTALL | re.MULTILINE
    )
    # Also remove the themes import since we'll define get_theme_config locally
    renderer_code = re.sub(
        r'^# Import theme loader for dynamic theme selection\nfrom \.themes import get_theme_config',
        '# Theme loader defined locally',
        renderer_code,
        flags=re.MULTILINE
    )
    # Remove the helpers import
    renderer_code = re.sub(
        r'^# Import helper functions\nfrom \.helpers import ensure_timezone\n\n',
        '',
        renderer_code,
        flags=re.MULTILINE
    )
    exec(renderer_code, globals())

# Load theme validation function from themes.py
# We only need the REQUIRED_THEME_FIELDS constant and validate_custom_theme function
themes_file = component_dir / "themes.py"
with open(themes_file, 'r', encoding='utf-8') as f:
    themes_code = f.read()

# Load themes.json for the get_theme_config function
themes_json_file = component_dir / "themes.json"
with open(themes_json_file, 'r', encoding='utf-8') as f:
    _THEMES_DATA = json.load(f)

# Extract REQUIRED_THEME_FIELDS and validate_custom_theme function
REQUIRED_THEME_FIELDS = {
    "axis_label_color", "background_color", "cheap_price_color", "fill_alpha", "fill_color",
    "grid_alpha", "grid_color", "label_color", "label_color_avg", "label_color_max",
    "label_color_min", "label_stroke", "nowline_alpha", "nowline_color", "plot_linewidth",
    "price_line_color", "price_line_color_above_avg", "price_line_color_below_avg",
    "price_line_color_near_avg", "spine_color", "tick_color", "tickline_color",
}

def validate_custom_theme(theme_config):
    """Validate that a custom theme contains all required fields."""
    if not isinstance(theme_config, dict):
        return False, "Theme config must be a dictionary"

    missing_fields = REQUIRED_THEME_FIELDS - set(theme_config.keys())

    if missing_fields:
        return False, f"Missing required theme fields: {', '.join(sorted(missing_fields))}"

    return True, ""

def get_theme_config(theme_name, custom_theme=None):
    """Get configuration for a specific theme or use custom theme."""
    if custom_theme is not None:
        return custom_theme

    if theme_name not in _THEMES_DATA:
        print(f"Warning: Theme '{theme_name}' not found, falling back to 'dark' theme")
        theme_name = "dark"

    return _THEMES_DATA[theme_name]

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
import json
from PIL import Image, ImageDraw

# Configuration
OUTPUT_FILE = Path(__file__).parent / "local_render.png"
PRICE_DATA_FILE = Path(__file__).parent / "local_render.json"
# Width, height, and currency are loaded from const.py:
# - CANVAS_WIDTH and CANVAS_HEIGHT
# - CURRENCY_OVERRIDE

# Local timezone
LOCAL_TZ = tz.tzlocal()

# Process and validate custom theme if provided
custom_theme_config = None
if custom_theme_json:
    try:
        custom_theme_config = json.loads(custom_theme_json)
        print(f"Parsed custom theme JSON successfully")

        # Validate the custom theme using the validation function from themes.py
        is_valid, error_message = validate_custom_theme(custom_theme_config)
        if not is_valid:
            print(f"Error: Invalid custom theme configuration - {error_message}")
            sys.exit(1)

        print(f"✓ Custom theme validated successfully")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in custom theme - {e}")
        sys.exit(1)


def publish_image(image_path, resize_width=590, border_width=1, border_color=(61, 61, 61), corner_radius=10):
    """Prepare image for publishing: resize, add border/rounded corners, convert transparent to black background.

    Args:
        image_path: Path to the image file to modify
        resize_width: Target width in pixels (default: 590)
        border_width: Width of the border in pixels (default: 1)
        border_color: RGB tuple for border color (default: dark gray (61, 61, 61))
        corner_radius: Radius for rounded corners in pixels (default: 10)
    """
    img = Image.open(image_path)

    # Step 1: Resize to target width
    if resize_width:
        original_size = img.size
        aspect_ratio = original_size[1] / original_size[0]
        new_height = int(resize_width * aspect_ratio)
        img = img.resize((resize_width, new_height), Image.LANCZOS)
        print(f"  → Resized from {original_size[0]}x{original_size[1]} to {resize_width}x{new_height}")

    width, height = img.size

    # Step 2: Determine if we need to add a black background (for transparent images)
    convert_transparent = img.mode == 'RGBA'

    # Step 3: Apply rounded corners with appropriate background
    if convert_transparent:
        # For transparent images, keep corners transparent and convert only the content area to black background
        from PIL import ImageChops

        # First, flatten the transparent image onto black background
        black_bg = Image.new('RGB', (width, height), (0, 0, 0))
        black_bg.paste(img, (0, 0), img)

        # Create rounded corner mask (use same coordinates as border will use)
        mask = Image.new('L', (width, height), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle([(0, 0), (width - 1, height - 1)], corner_radius, fill=255)

        # Convert flattened image to RGBA
        black_bg_rgba = black_bg.convert('RGBA')

        # Use the mask as the alpha channel (corners will be transparent)
        r, g, b, _ = black_bg_rgba.split()
        result = Image.merge('RGBA', (r, g, b, mask))

        print(f"  → Converted transparent background to black with transparent rounded corners")
    else:
        # For RGB images, just apply rounded corners
        # Sample corners to detect background color
        corner_pixels = [
            img.getpixel((0, 0)),
            img.getpixel((width-1, 0)),
            img.getpixel((0, height-1)),
            img.getpixel((width-1, height-1))
        ]
        avg_brightness = sum(sum(pixel[:3]) for pixel in corner_pixels) / (len(corner_pixels) * 3)
        bg_color = (0, 0, 0) if avg_brightness < 128 else (255, 255, 255)

        result = Image.new('RGB', (width, height), bg_color)
        mask = Image.new('L', (width, height), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle([(0, 0), (width - 1, height - 1)], corner_radius, fill=255)
        result.paste(img, (0, 0), mask)
        print(f"  → Applied rounded corners")

    # Step 4: Draw border
    draw = ImageDraw.Draw(result)
    if result.mode == 'RGBA':
        draw.rounded_rectangle(
            [(0, 0), (width - 1, height - 1)],
            corner_radius,
            outline=border_color + (255,),  # Add alpha channel for RGBA
            width=border_width
        )
    else:
        draw.rounded_rectangle(
            [(0, 0), (width - 1, height - 1)],
            corner_radius,
            outline=border_color,
            width=border_width
        )
    print(f"  → Added {border_width}px border")

    # Save the result
    result.save(image_path)


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
        parsed_time = parse_time_string(fixed_time, now.date())
        if parsed_time is None:
            print(f"Error: Invalid time format '{fixed_time}'. Use HH:MM or HH:MM:SS format (e.g., 19:34)")
            sys.exit(1)
        now = parsed_time

    # Get today's and tomorrow's dates for dynamic date generation
    today = now.date()
    tomorrow = today + datetime.timedelta(days=1)

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

            # Determine which day we're in for price adjustments
            hour = interval_time.hour

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
            if interval_time.date() > today:
                # Adjust second day to be slightly lower on average
                base_price *= random.uniform(0.85, 0.95)

            price = max(0.50, base_price + variation)  # Ensure price doesn't go too low
            prices.append(price)

        return dates, prices, now

    # Load real price data from JSON file
    # Note: This file format matches the expected format for entity-based price data
    # (same format as entity attributes 'prices' or 'data')
    # Supported field names: `start_time|start|startsAt` for timestamp, `price|price_per_kwh|total` for value
    try:
        with open(PRICE_DATA_FILE, 'r', encoding='utf-8') as f:
            price_data_json = json.load(f)
    except FileNotFoundError:
        print(f"Error: Price data file not found: {PRICE_DATA_FILE}")
        print("Tip: Use --random flag to generate random data instead.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {PRICE_DATA_FILE}: {e}")
        sys.exit(1)

    if not price_data_json:
        print(f"Error: No price data found in {PRICE_DATA_FILE}")
        sys.exit(1)

    # Use shared helper to load and process price data
    # This includes date mapping and filtering (today+tomorrow only by default)
    dates, prices, date_mapping = load_price_data_from_json(
        PRICE_DATA_FILE,
        reference_date=today,
        start_graph_at=None,  # Use default filtering (today+tomorrow)
        include_all=False
    )

    # Print date mapping information
    if date_mapping:
        sorted_original = sorted(date_mapping.keys())
        print(f"JSON contains data for {len(sorted_original)} day(s): {', '.join(str(d) for d in sorted_original)}")

        # Show mapping details
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        for original_date in sorted_original:
            mapped_date = date_mapping[original_date]
            if mapped_date == yesterday:
                label = "yesterday"
            elif mapped_date == today:
                label = "today"
            elif mapped_date == tomorrow:
                label = "tomorrow"
            else:
                days_from_tomorrow = (mapped_date - tomorrow).days
                label = f"tomorrow+{days_from_tomorrow}"
            print(f"Mapping: {original_date} → {label}")

    return dates, prices, now


def main():
    """Generate test render."""
    # Define render_options based on config_mode
    if config_mode == 'defaults':
        # Pure defaults - no overrides
        render_options = None
        print("Using defaults only (no render options)")
    elif config_mode == 'old_defaults':
        # Old default values (before recent changes to defaults.py)
        render_options = {
            # General settings
            "canvas_width": 1200,  # Override: increased width for watch (default: 1180)
            "canvas_height": 700,  # Override: square for watch (default: 820)
            "color_price_line_by_average": False,  # Old default: single color price line (new default: True)
            # Price labels
            "label_current": "on_in_graph",  # Old default: show current label on graph (new default: "on")
            # Y-axis settings
            "show_y_axis": "on_with_tick_marks",  # Old default: show Y-axis tick marks (new default: "on")
        }
        print("Using old default values (Y-axis ticks visible, current label on graph, single color price line)")
    elif config_mode == 'test':
        # Test configuration: light theme with colored labels (only overrides from defaults)
        render_options = {
            # General settings
            "theme": "light",  # Override: light instead of dark (default: dark)
            "cheap_price_points": 5,  # Override: highlight 20 cheapest periods per day (default: 0)
            "cheap_price_threshold": 1.0,  # Override: highlight periods below 100 öre (default: 0)
            "color_price_line_by_average": False,  # Override: use single color price line (default: True)
            # Price labels
            "use_hourly_prices": True,  # Override: aggregate to hourly (default: False)
            "label_current": "on_in_graph",  # Override: show current label on graph instead of in header (default: "on")
            "label_min": "off",  # Override: hide min label (default: "on")
            "label_max": "off",  # Override: hide max label (default: "on")
            # X-axis settings
            "show_x_axis": "on_with_tick_marks",  # Override: show X-axis with tick marks (default: "on")
            "cheap_periods_on_x_axis": "on",  # Override: show cheap periods in separate row (default: "off")
            "show_vertical_grid": False,  # Override: hide vertical grid (default: True)
            # Y-axis settings
            "y_tick_count": 3,  # Override: 3 ticks instead of automatic (default: None)
            "y_tick_use_colors": True,  # Override: colored ticks (default: False)
        }
        print("Using test configuration: light theme, colored labels")
    else:  # wearos
        # Wear OS configuration (only overrides from defaults)
        render_options = {
            # General settings
            "theme": "dark",  # Override: dark theme (default: dark)
            "transparent_background": True,  # Override: transparent background (default: False)
            "canvas_width": 1280,  # Override: increased width for watch (default: 1180)
            "canvas_height": 720,  # Override: square for watch (default: 820)
            "label_font_size": 17,  # Override: larger font (default: 11)
            "start_graph_at": "current_hour",  # Override: start at current hour (default: midnight)
            "cheap_price_points": 5,  # Override: highlight 5 cheapest periods per day (default: 0)
            "cheap_price_threshold": 0.5,  # Override: highlight periods below 50 öre (default: 0)
            # Price labels
            "use_hourly_prices": True,  # Override: aggregate to hourly (default: False)
            "use_cents": True,  # Override: display in cents (default: False)
            "currency_override": "öre",  # Override: display "öre" instead of "¢" (default: None)
            "label_current": "on_current_price_only",  # Override: show current price only in header (default: "on")
            "label_min": "on_no_price",  # Override: show only time on min label (default: "on")
            "label_max": "on_no_price",  # Override: show only time on max label (default: "on")
            # X-axis settings
            "show_x_axis": "on_with_tick_marks",  # Override: show X-axis with tick marks (default: "on")
            "cheap_periods_on_x_axis": "on_comfy",  # Override: show cheap periods in separate row (default: "off")
            # Y-axis settings
            "show_y_axis": "on_with_tick_marks", # Override: show Y-axis tick marks (default: "on")
            "y_tick_count": 2,  # Override: 3 ticks instead of automatic (default: None)
            "y_axis_label_rotation_deg": 270,  # Override: vertical labels for right side (default: 0)
            "y_axis_side": "right",  # Override: Y-axis on right (default: left)
            "y_tick_use_colors": True,  # Override: colored ticks (default: False)
        }
        print("Using Wear OS configuration: dark theme, hourly prices, öre currency")

    # Apply custom theme if provided
    if custom_theme_config:
        if render_options is None:
            render_options = {}
        render_options["custom_theme"] = custom_theme_config
        print("Applied custom theme to render options")

    print("Generating sample price data...")
    dates_raw, prices_raw, now_local = generate_price_data(
        use_random=use_random_data,
        fixed_time=fixed_time
    )

    # Determine if we should use hourly prices
    use_hourly = render_options.get("use_hourly_prices", USE_HOURLY_PRICES) if render_options else USE_HOURLY_PRICES

    # Aggregate to hourly prices if configured (using camera.py's method)
    if use_hourly:
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
        step_minutes = int((dates_raw[1] - dates_raw[0]).total_seconds() // 60) or (60 if use_hourly else 15)
    else:
        step_minutes = 60 if use_hourly else 15

    interval_td = datetime.timedelta(minutes=step_minutes)
    dates_plot = dates_raw + [dates_raw[-1] + interval_td]
    prices_plot = prices_raw + [prices_raw[-1]]

    print(f"Data range: {dates_raw[0].strftime('%Y-%m-%d %H:%M')} to {dates_raw[-1].strftime('%Y-%m-%d %H:%M')}")
    print(f"Current time: {now_local.strftime('%Y-%m-%d %H:%M')}")
    print(f"Data points: {len(dates_raw)} ({'hourly' if use_hourly else '15-minute'} intervals)")
    print(f"Current price index: {idx}")
    print(f"Price range: {min(prices_raw):.4f} - {max(prices_raw):.4f}")
    print(f"Current price: {prices_raw[idx]:.4f}")

    # Get currency: override if set, otherwise auto-select based on cents mode
    use_cents_opt = render_options.get("use_cents", USE_CENTS) if render_options else USE_CENTS

    if render_options and "currency_override" in render_options:
        currency_override = render_options["currency_override"]
    else:
        currency_override = CURRENCY_OVERRIDE

    if currency_override:
        currency = currency_override
    elif use_cents_opt:
        currency = "¢"
    else:
        currency = "SEK"

    # Get canvas size from render_options or globals
    canvas_width = render_options.get("canvas_width", CANVAS_WIDTH) if render_options else CANVAS_WIDTH
    canvas_height = render_options.get("canvas_height", CANVAS_HEIGHT) if render_options else CANVAS_HEIGHT

    print(f"\nRendering to {OUTPUT_FILE}...")
    print(f"Active configuration:")
    print(f"  - Mode: {config_mode}")
    print(f"  - Canvas size: {canvas_width}x{canvas_height}")
    print(f"  - Currency: {currency}")
    if render_options:
        print(f"  - Theme: {render_options.get('theme', 'default')}")
        print(f"  - Colored labels: {render_options.get('label_use_colors', False)}")
        print(f"  - Colored Y ticks: {render_options.get('y_tick_use_colors', False)}")

    render_plot_to_path(
        width=canvas_width,
        height=canvas_height,
        dates_plot=dates_plot,
        prices_plot=prices_plot,
        dates_raw=dates_raw,
        prices_raw=prices_raw,
        now_local=now_local,
        idx=idx,
        currency=currency,
        out_path=OUTPUT_FILE,
        render_options=render_options,
    )

    print(f"✓ Successfully rendered to {OUTPUT_FILE}")

    # Apply publish mode if requested
    if publish_mode:
        print(f"\nPreparing image for publishing...")
        try:
            publish_image(OUTPUT_FILE, resize_width=590, border_width=1, border_color=(61, 61, 61), corner_radius=10)
            print(f"✓ Image prepared for publishing")
        except Exception as e:
            print(f"✗ Failed to prepare image: {e}")

    print("\nYou can now open the image to see the result!")


if __name__ == "__main__":
    main()
