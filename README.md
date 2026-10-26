# Heightmap terrain mesh

This program turns a grayscale heightmap into a solid 3D terrain model. Light areas become high ground, and dark areas become low ground. You can choose the model's width and height, then save it as an STL file for 3D printing.

![A 3D hill made from the sample heightmap](examples/terrain-preview.png)

## How the model is made

A heightmap stores height as the brightness of each pixel. The program puts those pixels on a grid and turns each group of four neighboring points into two triangles. These triangles make the top surface. More triangles form the bottom and side walls so the model is closed.

The program can read 8-bit and 16-bit grayscale images. A 16-bit image can store more height levels. Color images are converted to grayscale before the model is built.

The sample image is a generated hill. A normal picture of a map with contour lines will not work the same way. The input needs to store elevation as pixel brightness. The program does not look up geographic heights or convert map projections.

## Controlling the size

| Option | What it changes |
| --- | --- |
| `--width-mm` | The full width of the model in millimeters |
| `--spacing` | The distance between original pixel centers if width is not set |
| `--relief` | The height from the lowest ground to the highest ground |
| `--height-scale` | Height per brightness level when relief is not set |
| `--base-thickness` | How far the bottom sits below the lowest ground |
| `--base` | The bottom's Z coordinate when base thickness is not set |
| `--max-size` | The largest allowed grid dimension |
| `--smooth` | How much to smooth the input image |
| `--crop` | A rectangle to cut from the input before building the model |

Width and depth follow the shape of the cropped image's grid. Without `--width-mm`, the default spacing is 1 mm. Pixel centers define the boundary, so a 201 by 101 pixel image spans 200 by 100 mm at that spacing. X follows image columns and Y follows image rows. The image is not flipped.

The default maximum grid size is 256 pixels on its longest side. If the image is bigger, the program reduces the number of points while keeping the physical size the same. This makes the STL smaller. A 256 by 256 grid already has about 262,000 triangles.

`--relief 20` maps the lowest brightness in the prepared image to 0 mm and the highest to 20 mm. A constant image stays flat. Without relief, the default height scale is 0.1 mm per brightness level. Relief is often easier to use with 16-bit images because their values can be much larger.

Smoothing uses a Gaussian blur before the grid is resized. Its strength is measured in input pixels. A crop uses X, Y, width, and height and must be at least two pixels wide and tall.

## Checking the mesh

Before saving, the program checks for open edges, edges shared by too many triangles, faces pointing the wrong way around a shared edge, and triangles with no area. It also checks that the signed volume is positive. These checks help catch problems with how the surface is joined together. They do not check every possible self-intersection or choose printer settings.

The JSON report includes the dimensions, volume, surface area, triangle count, grid spacing, and check results. The preview shows only the top surface. The report includes the whole solid, including the base. The bottom must sit below the lowest terrain point.

All measurements use millimeters. STL files do not store units, so use millimeters when you open the file in another program.

## Try it

Use Python 3.11 or newer. Open a terminal in this project's folder and create a virtual environment. This keeps its packages separate from your other Python projects.

```sh
python -m venv .venv
```

On Windows, activate it with this command.

```sh
.venv\Scripts\activate
```

On macOS or Linux, use this command instead.

```sh
source .venv/bin/activate
```

Then install the packages the project needs.

```sh
python -m pip install -r requirements.txt
```

```sh
python sample_heightmap.py
python terrain.py heightmap.png --width-mm 100 --relief 20 --base-thickness 3 --preview preview.png
```

The example saves `terrain.stl`, `terrain.json`, and `preview.png`. Open the STL in a slicer to inspect it before printing.

```sh
python terrain.py heightmap.png --width-mm 150 --relief 25 --base-thickness 4 --max-size 128 --smooth 1.5
python terrain.py heightmap.png --crop 10 5 40 30 --width-mm 80 --relief 12 --output cropped.stl
python terrain.py heightmap.png --spacing 0.5 --height-scale 0.05 --base -2
```

Use `--report` to choose where the JSON report is saved. Otherwise, it is placed beside the STL. `--base-thickness` takes priority over `--base`, and `--relief` takes priority over `--height-scale`.

The Python functions can also be used on their own.

```python
from heightfield import load_heightmap, prepare
from terrain import build_terrain
from mesh_checks import inspect_mesh

image = load_heightmap('heightmap.png')
heights, spacing = prepare(image, width_mm=100, relief=20, max_size=128)
solid = build_terrain(heights, spacing=spacing, height_scale=1, base=-3)
print(inspect_mesh(solid))
solid.save('terrain.stl')
```

## Tests

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The tests check known block volumes, saved STL files, shared edges, reversed faces, open surfaces, physical size after resizing, 16-bit input, smoothing, crops, and invalid settings. GitHub Actions runs the same tests.
