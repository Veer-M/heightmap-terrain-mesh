import argparse
import json
import math
from pathlib import Path
import numpy as np
from stl import mesh, Mode
from heightfield import load_heightmap, prepare
from mesh_checks import inspect_mesh, preview

def build_terrain(image, spacing=1.0, height_scale=0.1, base=-5.0):
    image = np.asarray(image)
    if image.ndim != 2 or min(image.shape) < 2 or not np.isfinite(image).all():
        raise ValueError('Heightmap must be a finite 2D grid of at least 2x2 pixels')
    sx,sy = (spacing,spacing) if np.isscalar(spacing) else spacing
    if not all(math.isfinite(v) for v in (sx,sy,height_scale,base)) or min(sx,sy) <= 0 or height_scale < 0:
        raise ValueError('Spacing must be positive and height scale nonnegative')
    if base >= float(image.min()) * height_scale:
        raise ValueError('Base must be below the lowest terrain point')
    height, width = image.shape
    triangles = []
    def top(x,y):
        return (x*sx,y*sy,float(image[y,x])*height_scale)
    def bottom(x,y):
        return (x*sx,y*sy,base)
    for y in range(height-1):
        for x in range(width-1):
            a,b,c,d = top(x,y),top(x+1,y),top(x+1,y+1),top(x,y+1)
            triangles.extend([(a,b,c),(a,c,d)])
            a,b,c,d = bottom(x,y),bottom(x+1,y),bottom(x+1,y+1),bottom(x,y+1)
            triangles.extend([(a,c,b),(a,d,c)])
    boundary = ([(x,0) for x in range(width)] + [(width-1,y) for y in range(1,height)]
                + [(x,height-1) for x in range(width-2,-1,-1)] + [(0,y) for y in range(height-2,0,-1)])
    for i, point in enumerate(boundary):
        following = boundary[(i+1)%len(boundary)]
        a,b,c,d = top(*point),bottom(*point),bottom(*following),top(*following)
        triangles.extend([(a,b,c),(a,c,d)])
    result = mesh.Mesh(np.zeros(len(triangles), dtype=mesh.Mesh.dtype))
    result.vectors[:] = np.array(triangles)
    result.update_normals()
    return result

def main():
    parser = argparse.ArgumentParser(description='Create a closed terrain STL from a grayscale heightmap')
    parser.add_argument('image', nargs='?', default='heightmap.png')
    parser.add_argument('--output', default='terrain.stl')
    parser.add_argument('--spacing', type=float, default=1)
    parser.add_argument('--height-scale', type=float, default=0.1)
    parser.add_argument('--base', type=float, default=-5)
    parser.add_argument('--base-thickness',type=float,help='Place bottom this far below the lowest height')
    parser.add_argument('--width-mm',type=float,help='Set total model width and preserve image aspect ratio')
    parser.add_argument('--relief',type=float,help='Normalize grayscale range to this height in millimeters')
    parser.add_argument('--max-size',type=int,default=256,help='Maximum grid dimension')
    parser.add_argument('--smooth',type=float,default=0,help='Gaussian smoothing sigma in input pixels')
    parser.add_argument('--crop',type=int,nargs=4,metavar=('X','Y','WIDTH','HEIGHT'))
    parser.add_argument('--preview',help='Save a PNG preview of the prepared surface')
    parser.add_argument('--report',help='JSON report path; defaults beside the STL')
    args = parser.parse_args()
    try:
        image = load_heightmap(args.image)
        elevations,spacing = prepare(image,args.spacing,args.width_mm,args.max_size,args.smooth,
                                     args.height_scale,args.relief,args.crop)
        if args.base_thickness is not None:
            if not math.isfinite(args.base_thickness) or args.base_thickness <= 0:
                raise ValueError('Base thickness must be positive and finite')
            base = float(elevations.min())-args.base_thickness
        else:
            base = args.base
        result = build_terrain(elevations,spacing,1.0,base)
        report = inspect_mesh(result)
        if not report['watertight'] or report['signed_volume_mm3'] <= 0:
            raise ValueError('Generated mesh failed topology or volume checks')
    except ValueError as error:
        parser.error(str(error))
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    result.save(args.output, mode=Mode.BINARY)
    report['grid_shape'] = list(elevations.shape)
    report['grid_spacing_mm'] = list(spacing)
    report_path = Path(args.report) if args.report else Path(args.output).with_suffix('.json')
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if args.preview:
        Path(args.preview).parent.mkdir(parents=True,exist_ok=True)
        preview(elevations,spacing,args.preview)
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
