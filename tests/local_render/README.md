# Local Rendering Tests

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
python local_render.py
```

To use only the base configuration (ignoring test overrides):

```bash
python local_render.py --no-override
```

This will:

- Generate sample price data (48 hours in 15-minute intervals, from midnight today through tomorrow)
- Render the graph using your current configuration (`defaults.py` + component `config.py` + test `config.py`)
- Save the output as `local_render.png` in the current directory

## Configuration Hierarchy

The component uses a three-level configuration system:

1. **defaults.py** (component) - Base defaults (don't edit this)
2. **config.py** (component) - User/production configuration overrides
3. **config.py** (tests/local_render) - Test-specific overrides

## Making Cosmetic Changes

1. Edit your user configuration in `../../custom_components/tibber_graph/config.py`
2. (Optional) Override specific settings for testing by editing `config.py` in this directory
3. Run `python local_render.py` from the local_render directory to see the changes
4. Open `local_render.png` to view the result
5. Repeat until satisfied!

This workflow is much faster than reloading the component in Home Assistant for every visual tweak.

## Test Configuration Overrides

The `config.py` file in this directory allows you to override specific settings for testing purposes without modifying your production configuration. This is useful for:

- Testing with different currencies
- Testing with different display modes (cents vs. full units)
- Testing different time ranges (midnight-to-midnight vs. current hour)
- Testing different themes or canvas sizes

Simply edit `config.py` in the test directory to override any setting you want to test.

## Output

The local render script generates a PNG image with:

- 48 hours of sample data in 15-minute intervals (192 data points total)
- Covers today (from midnight) and tomorrow
- Realistic price patterns (cheaper at night, more expensive during peak hours)
- Current time marker
- Price labels based on your configuration

The output file (`local_render.png`) is automatically ignored by git.
