# Tibber Graph UI Test

A local web-based UI for testing and previewing Tibber Graph configuration options with a Home Assistant-inspired interface.

## Overview

This test UI provides a browser-based interface for configuring and previewing the Tibber Graph integration without needing a full Home Assistant installation. Perfect for:

- 🧪 Testing configuration changes
- 🎨 Experimenting with visual options
- 📸 Taking screenshots for documentation
- 🐛 Debugging rendering issues
- 🚀 Developing new features

## Features

✨ **Home Assistant-Style Dark Mode UI**: Clean, modern dark interface matching Home Assistant's design language
🎨 **Live Auto-Preview**: Configuration changes automatically render in real-time
⚙️ **All Configuration Options**: Test every available configuration parameter
📊 **Real Tibber Data**: Uses actual price data from `local_render.json`
⏰ **Time Simulation**: Test how the graph looks at different times of day

## Quick Start

### 1. Install Dependencies

```powershell
cd tests\ui_test
pip install -r requirements.txt
```

### 2. Run the Server

```powershell
python app.py
```

### 3. Open in Browser

Navigate to: `http://localhost:5000`

The UI will automatically render a preview with default settings when you first open the page.

## Usage

### Configuration Sections

The UI is organized into sections matching the Home Assistant options flow:

- **General Settings**: Theme, canvas size, fixed size mode
- **X-Axis Settings**: Tick display, midnight start, step hours
- **Y-Axis Settings**: Axis display, grid, label rotation, side, tick count, colors
- **Price Label Settings**: Hourly mode, cents, currency, label options, colors, decimals
- **Auto-Refresh Settings**: Enable/disable auto-refresh
- **Test Options**: Time simulation

### Testing Workflow

1. **Adjust Configuration**: Modify any settings in the left sidebar
2. **See Changes Instantly**: The graph automatically re-renders when you change any option
3. **Reset**: Click "Reset to Defaults" to restore all defaults and re-render

### Test Options

**Simulate Time**
- Enter a time in `HH:MM` format (e.g., `19:34`) to simulate how the graph looks at that specific time
- Press Enter or click outside the field to trigger re-render
- Leave empty to use current time

## Data Source

The UI uses the price data from `tests/local_render.json`. This file must exist for the UI to work. You can generate or update this file using the existing `local_render.py` script with real Tibber data.

## Requirements

- Python 3.8+
- Flask 3.0+
- python-dateutil 2.8+

All dependencies from the main Tibber Graph component are loaded dynamically (matplotlib, numpy, etc.).

## Architecture

The UI test application consists of:

- **`app.py`**: Flask web server with routes for rendering and configuration
- **`templates/index.html`**: Home Assistant-style HTML interface
- **`static/style.css`**: CSS styling matching Home Assistant design
- **Integration with `local_render/`**: Reuses the existing rendering utilities

The application dynamically loads the Tibber Graph component code (`defaults.py`, `renderer.py`, `camera.py`) without requiring Home Assistant dependencies.

## Troubleshooting

**Issue**: "Failed to load price data"
- **Solution**: Ensure a valid `local_render.json` file exists in `tests/`. You can create it using the `local_render.py` script in `tests/local_render/`.

**Issue**: Graph doesn't render
- **Solution**: Check the browser console (F12) for JavaScript errors and the terminal for Python errors.

**Issue**: Port 5000 already in use
- **Solution**: Edit `app.py` and change the port in the last line: `app.run(debug=True, port=5001)`

**Issue**: Changes don't auto-render
- **Solution**: For text inputs like "Simulate Time", press Enter or click outside the field to trigger the change event.

## Development

To modify the UI:

1. **Layout/Content**: Edit `templates/index.html`
2. **Styling**: Edit `static/style.css`
3. **Backend Logic**: Edit `app.py`

The Flask server runs in debug mode by default, so changes to Python files will auto-reload. Browser refresh is needed for HTML/CSS changes.

## Comparison with local_render

While `tests/local_render/local_render.py` is a CLI tool for batch rendering, this UI test provides:

- Interactive visual configuration with dark mode
- Immediate automatic feedback on changes
- No command-line expertise required
- Better suited for exploring options and finding the perfect configuration
- Real-time preview as you adjust settings

Both tools share the same underlying rendering code, ensuring consistency.

## License

Same as the main Tibber Graph integration.
