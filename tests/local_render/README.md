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
python local_render.py                 # Test configuration (defaults.py + test config.py)
python local_render.py --no-override   # Component configuration (defaults.py + component config.py)
python local_render.py --defaults-only # Pure defaults (only defaults.py, no overrides)
```

This will:

- Generate sample price data (48 hours in 15-minute intervals, from midnight today through tomorrow)
- Render the graph using your current configuration (see below)
- Save the output as `local_render.png` in the current directory

## Configuration

The script supports three configuration modes:

**Default mode** (no arguments):

1. `/custom_components/tibber_graph/defaults.py` - Base defaults
2. `/tests/local_render/config.py` - Test-specific overrides

**Component mode** (`--no-override`):

1. `/custom_components/tibber_graph/defaults.py` - Base defaults
2. `/custom_components/tibber_graph/config.py` - User/production configuration

**Defaults only mode** (`--defaults-only`):

1. `/custom_components/tibber_graph/defaults.py` - Base defaults only (no overrides)

## Making changes

1. (Optional) Make changes to the configuration (see above) or component code in `../../custom_components/tibber_graph`
2. (Optional) Override specific settings for testing by editing `/tests/local_render/config.py`
3. Run `python local_render.py`
4. Open `local_render.png` to see your changes in action
5. Repeat until satisfied!
