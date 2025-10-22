# Local rendering

This directory contains tools for rendering and testing the Tibber Graph locally without needing to load it into Home Assistant.

## Setup

1. Navigate to the local_render directory:

   ```bash
   cd tests/local_render
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the local render script to generate a sample graph:

```bash
python local_render.py                    # Test mode: light theme with colored labels (default)
python local_render.py --my               # Use my settings (dark theme, hourly prices, öre currency)
python local_render.py --defaults         # Use only defaults.py (pure defaults, no overrides)
python local_render.py --random           # Use random generated price data instead of real Tibber data
python local_render.py --time 19:34       # Simulate a specific time (e.g., 19:34 today)
```

This will:

- Generate sample price data (48 hours in 15-minute intervals, from midnight today through tomorrow)
- Render the graph using the selected configuration mode
- Save the output as `local_render.png` in the current directory

## Configuration Modes

The script supports three configuration modes:

**Test mode** (default, no arguments):

- Uses `defaults.py` as base
- Applies inline render options: light theme, colored labels, colored Y-axis ticks

**My mode** (`--my`):

- Uses `defaults.py` as base
- Dark theme, hourly prices, öre currency, colored Y-ticks

**Defaults only mode** (`--defaults`):

- Uses only `custom_components/tibber_graph/defaults.py`
- No overrides or customizations applied
- Shows pure default appearance

## Making changes

1. Make changes to the component code in `../../custom_components/tibber_graph`
2. Run `python local_render.py` (test mode) or `python local_render.py --my`
3. Open `local_render.png` to see your changes in action
4. Repeat until satisfied!

## Customizing Test Mode

To customize the test mode render options, edit the `render_options` dictionary in `local_render.py`:

```python
render_options = {
    "theme": "light",              # "light" or "dark"
    "label_use_colors": True,      # Color min/max labels
    "y_tick_use_colors": True,     # Color Y-axis ticks
    # Add other options as needed
}
```
