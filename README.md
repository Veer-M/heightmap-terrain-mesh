# Heightmap terrain mesh

This turns a grayscale image into a solid terrain STL. Bright pixels become high ground, and a flat bottom plus side walls close the model for printing.

## Run it

Use Python 3.11 or newer. Run these commands from this repository's folder.

```sh
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
```

```sh
python sample_heightmap.py
python terrain.py heightmap.png --output terrain.stl
python terrain.py heightmap.png --spacing 0.5 --height-scale 0.05
```

## How it works and current limits

One image pixel spans 1 mm by default, and intensity 255 becomes 25.5 mm above Z=0. The bottom is Z=-5 mm. Images are treated as heights, not contour maps; geographic elevations and map scale must be supplied separately. Every pixel adds geometry, so resize large images first.

## Tests

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests check that each mesh edge is shared by two faces with opposite directions, volume is positive, and the STL can be loaded again.
