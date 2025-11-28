"""Local UI test application for Tibber Graph configuration.

This Flask application provides a Home Assistant-like interface for testing
the Tibber Graph configuration options and viewing the rendered output in real-time.

Usage:
    python app.py

Then open http://localhost:5000 in your browser.
"""
import datetime
import io
import json
import sys
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify

# Import shared test helpers
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_helpers import load_price_data_from_json, parse_time_string

# Add the local_render directory to the path to use its utilities
local_render_dir = Path(__file__).parent.parent / "local_render"
sys.path.insert(0, str(local_render_dir))

# Load the component directory path
component_dir = Path(__file__).parent.parent.parent / "custom_components" / "tibber_graph"

# Price data file location (in local/local_render/ folder)
PRICE_DATA_FILE = Path(__file__).parent.parent / "local_render" / "local_render.json"

# Load strings.json to get the list of available options
strings_file = component_dir / "strings.json"
with open(strings_file, 'r', encoding='utf-8') as f:
    strings_data = json.load(f)
    AVAILABLE_OPTIONS = list(strings_data['options']['step']['init']['data'].keys())

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

# Load themes.py using importlib to avoid import issues
import importlib.util
spec = importlib.util.spec_from_file_location("themes", component_dir / "themes.py")
themes_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(themes_module)
get_theme_config = themes_module.get_theme_config

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
    # Remove both import blocks: from .const and from .themes
    renderer_code = re.sub(
        r'# Import default constants from const\.py.*?\)',
        '# Constants already loaded from defaults.py and const.py',
        renderer_code,
        flags=re.DOTALL
    )
    # Remove the themes import
    renderer_code = re.sub(
        r'# Import theme loader.*?from \.themes import get_theme_config',
        '',
        renderer_code,
        flags=re.DOTALL
    )
    # Remove the helpers import
    renderer_code = re.sub(
        r'# Import helper functions\nfrom \.helpers import ensure_timezone\n\n',
        '',
        renderer_code
    )
    exec(renderer_code, globals())

# Import the aggregation function from camera.py
camera_file = component_dir / "camera.py"
with open(camera_file, 'r', encoding='utf-8') as f:
    camera_lines = f.readlines()
    in_method = False
    method_lines = []
    for i, line in enumerate(camera_lines):
        if 'def _aggregate_to_hourly(' in line:
            in_method = True
            method_lines.append(line.replace('    def _aggregate_to_hourly', 'def aggregate_to_hourly'))
        elif in_method:
            if line.strip() and not line.startswith(' ' * 8) and not line.startswith(' ' * 4 + '@'):
                break
            if line.startswith('        '):
                method_lines.append(line[4:])
            elif line.strip():
                method_lines.append(line)
            else:
                method_lines.append(line)
    aggregate_code = ''.join(method_lines)
    exec(aggregate_code, globals())

from dateutil import tz

app = Flask(__name__)

# Local timezone
LOCAL_TZ = tz.tzlocal()


def get_default_value(option_key):
    """Get the default value for a given option key from the loaded defaults.py globals."""
    # Convert option key to uppercase constant name
    const_name = option_key.upper()

    # Try to get the value from globals (loaded from defaults.py)
    value = globals().get(const_name)

    # Handle special cases where value might be None
    # Return empty string for UI display, but keep None for nullable options
    if option_key in ('y_tick_count', 'currency_override', 'hours_to_show', 'price_decimals') and value is None:
        return ''

    return value if value is not None else ''


def build_defaults_dict():
    """Build a dictionary of default values based on AVAILABLE_OPTIONS from strings.json."""
    defaults = {}
    for option_key in AVAILABLE_OPTIONS:
        defaults[option_key] = get_default_value(option_key)

    return defaults


def parse_option_value(option_key, form_value, default_fallback):
    """Parse a form value based on the option type."""
    # Boolean options (checkboxes)
    boolean_options = [
        'transparent_background', 'force_fixed_size',
        'show_horizontal_grid', 'show_average_price_line',
        'show_vertical_grid', 'y_tick_use_colors',
        'use_hourly_prices', 'use_cents',
        'show_data_source_name',
        'label_show_currency', 'label_use_colors',
        'color_price_line_by_average', 'show_cheap_price_line', 'label_minmax_per_day'
    ]

    # Integer options
    integer_options = [
        'canvas_width', 'canvas_height', 'x_tick_step_hours',
        'hours_to_show', 'cheap_price_points', 'cheap_price_threshold', 'y_axis_label_rotation_deg', 'y_tick_count',
        'label_font_size', 'price_decimals'
    ]

    # Float options
    float_options = ['cheap_price_threshold']

    # Integer options that can be empty
    nullable_string_options = ['currency_override', 'y_tick_count', 'hours_to_show']

    if option_key in boolean_options:
        return form_value == 'true'
    elif option_key in float_options:
        try:
            return float(form_value) if form_value else default_fallback
        except (ValueError, TypeError):
            return default_fallback
    elif option_key in integer_options:
        # Allow None for nullable integer options
        if option_key in ('y_tick_count', 'price_decimals', 'hours_to_show') and not form_value:
            return None
        try:
            return int(form_value) if form_value else default_fallback
        except (ValueError, TypeError):
            return default_fallback
    elif option_key in nullable_string_options:
        return form_value if form_value else None
    else:
        # String options (theme, y_axis_side, start_graph_at, currency_override)
        return form_value if form_value else default_fallback


def build_render_options(form_data):
    """Build render_options dictionary from form data based on AVAILABLE_OPTIONS."""
    render_options = {}

    for option_key in AVAILABLE_OPTIONS:
        default_value = get_default_value(option_key)
        form_value = form_data.get(option_key, '')

        render_options[option_key] = parse_option_value(option_key, form_value, default_value)

    # Handle hidden options not in strings.json (not exposed in UI but supported in YAML)
    hidden_options = ['cheap_boundary_highlight', 'show_cheap_price_line', 'label_use_colors', 'y_tick_use_colors', 'label_minmax_per_day', 'label_show_currency', 'show_data_source_name', 'data_source_name']
    for option_key in hidden_options:
        if option_key in form_data:
            default_value = get_default_value(option_key)
            form_value = form_data.get(option_key, '')
            render_options[option_key] = parse_option_value(option_key, form_value, default_value)

    # Auto-determine price_decimals if not explicitly set (None = auto)
    if render_options.get('price_decimals') is None:
        render_options['price_decimals'] = 0 if render_options.get('use_cents', False) else 2

    return render_options


def load_price_data(fixed_time=None, start_graph_at=None):
    """Load price data from JSON file.

    Args:
        fixed_time: Optional fixed time string (HH:MM) to simulate a different current time
        start_graph_at: Optional start_graph_at setting to filter data appropriately
    """
    now = datetime.datetime.now(LOCAL_TZ)

    if fixed_time:
        parsed_time = parse_time_string(fixed_time, now.date())
        if parsed_time is not None:
            now = parsed_time

    today = now.date()

    # Use shared helper to load and process price data
    try:
        dates, prices, date_mapping = load_price_data_from_json(
            PRICE_DATA_FILE,
            reference_date=today,
            start_graph_at=start_graph_at
        )
    except RuntimeError:
        return None, None, now

    return dates, prices, now


@app.route('/')
def index():
    """Render the main configuration page."""
    # Build defaults dictionary dynamically from strings.json options
    defaults = build_defaults_dict()

    return render_template('index.html', defaults=defaults)


@app.route('/render', methods=['POST'])
def render_graph():
    """Render the graph with the given configuration."""
    try:
        # Get form data
        data = request.json

        # Build render_options dynamically from strings.json options
        render_options = build_render_options(data)

        # Get additional parameters (not in strings.json options)
        fixed_time = data.get('fixed_time', '') or None

        # Load price data with start_graph_at option to handle filtering
        dates_raw, prices_raw, now_local = load_price_data(
            fixed_time=fixed_time,
            start_graph_at=render_options.get('start_graph_at')
        )

        if dates_raw is None or prices_raw is None:
            return jsonify({'error': 'Failed to load price data. Please ensure local_render.json exists in local/local_render/.'}), 400

        # Aggregate to hourly if configured
        if render_options['use_hourly_prices']:
            dates_raw, prices_raw = aggregate_to_hourly(dates_raw, prices_raw)

        # Find current price index
        idx = 0
        for i, date in enumerate(dates_raw):
            if date <= now_local:
                idx = i
            else:
                break

        # Prepare data for rendering
        if len(dates_raw) >= 2:
            step_minutes = int((dates_raw[1] - dates_raw[0]).total_seconds() // 60) or (60 if render_options['use_hourly_prices'] else 15)
        else:
            step_minutes = 60 if render_options['use_hourly_prices'] else 15

        interval_td = datetime.timedelta(minutes=step_minutes)
        dates_plot = dates_raw + [dates_raw[-1] + interval_td]
        prices_plot = prices_raw + [prices_raw[-1]]

        # Determine currency: override if set, otherwise auto-select based on cents mode
        if render_options['currency_override']:
            currency = render_options['currency_override']
        elif render_options['use_cents']:
            currency = "¢"
        else:
            currency = "SEK"

        # Render to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            render_plot_to_path(
                width=render_options['canvas_width'],
                height=render_options['canvas_height'],
                dates_plot=dates_plot,
                prices_plot=prices_plot,
                dates_raw=dates_raw,
                prices_raw=prices_raw,
                now_local=now_local,
                idx=idx,
                currency=currency,
                out_path=tmp_path,
                render_options=render_options,
            )

            # Read the file and send it
            with open(tmp_path, 'rb') as f:
                img_bytes = f.read()

            return send_file(io.BytesIO(img_bytes), mimetype='image/png')
        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(tmp_path)
            except:
                pass

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/defaults')
def get_defaults():
    """Return all default configuration values."""
    # Build defaults dictionary dynamically from strings.json options
    return jsonify(build_defaults_dict())


if __name__ == '__main__':
    print("=" * 70)
    print("Tibber Graph UI Test Server")
    print("=" * 70)
    print("\nStarting server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server.")
    print("=" * 70)
    app.run(debug=True, port=5000)
