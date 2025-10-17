# Tests

This directory contains various testing tools for the Tibber Graph component.

## Local Rendering Tests

See [local_render/](local_render/) for tools to render and test the graph locally without Home Assistant.

Quick start:

```bash
cd tests/local_render
pip install -r requirements.txt
python local_render.py
```

This is useful for quickly testing cosmetic changes (colors, fonts, layouts) without having to reload the component in Home Assistant.
