import argparse
import math
import cv2
import numpy as np
from stl import mesh, Mode

def build_terrain(image, spacing=1.0, height_scale=0.1, base=-5.0):
    image = np.asarray(image)
    if image.ndim != 2 or min(image.shape) < 2 or not np.isfinite(image).all():
        raise ValueError('Heightmap must be a finite 2D grid of at least 2x2 pixels')
    if not all(math.isfinite(v) for v in (spacing,height_scale,base)) or spacing <= 0 or height_scale < 0:
        raise ValueError('Spacing must be positive and height scale nonnegative')
    if base >= float(image.min()) * height_scale:
        raise ValueError('Base must be below the lowest terrain point')
    height, width = image.shape
    triangles = []
    def top(x,y):
        return (x*spacing,y*spacing,float(image[y,x])*height_scale)
    def bottom(x,y):
        return (x*spacing,y*spacing,base)
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
    args = parser.parse_args()
    image = cv2.imread(args.image, cv2.IMREAD_GRAYSCALE)
    if image is None:
        parser.error(f'Cannot read {args.image}')
    result = build_terrain(image,args.spacing,args.height_scale,args.base)
    result.save(args.output, mode=Mode.BINARY)
    print(f'Wrote {len(result.vectors)} triangles to {args.output}')

if __name__ == '__main__':
    main()
