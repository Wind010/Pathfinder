# Installation Guide

## Method 1: Install with pipx (Recommended)

Install directly from GitHub:
```bash
pipx install git+https://github.com/wind010/Pathfinder.git
```

Or install from a local clone:
```bash
git clone https://github.com/wind010/Pathfinder.git
cd Pathfinder
pipx install .
```

After installation, you can run:
```bash
pathfinder --ip 10.10.10.10 --hostname example.htb -o ./scans/example
```

## Method 2: Install with pip

```bash
pip install git+https://github.com/wind010/Pathfinder.git
```

Or from local:
```bash
pip install .
```

## Method 3: Development Mode

For development, install in editable mode:
```bash
pip install -e .
```

This allows you to make changes to the code without reinstalling.

## Method 4: Run Directly (No Installation)

You can still run the tool directly without installation:
```bash
python pathfinder.py --ip 10.10.10.10 --hostname example.htb -o ./scans/example
```

## Uninstalling

If installed with pipx:
```bash
pipx uninstall pathfinder-recon
```

If installed with pip:
```bash
pip uninstall pathfinder-recon
```

## Configuration File

After installation with pipx/pip, you'll need to provide a config file location:
```bash
pathfinder --ip 10.10.10.10 --hostname example.htb -o ./output -c /path/to/config.yaml
```

Or copy the default config to your working directory:
```bash
# The default config is included in the package
# You can create your own based on the example in the repository
curl -O https://raw.githubusercontent.com/wind010/Pathfinder/main/config.yaml
```

## Publishing to PyPI (For Maintainers)

To publish the package to PyPI:

1. Install build tools:
```bash
pip install build twine
```

2. Build the package:
```bash
python -m build
```

3. Upload to PyPI:
```bash
twine upload dist/*
```

After publishing, users can install with:
```bash
pipx install pathfinder-recon
```
