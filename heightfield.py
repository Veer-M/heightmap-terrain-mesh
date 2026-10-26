import math
import cv2
import numpy as np

def load_heightmap(path):
    image = cv2.imread(str(path),cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f'Cannot read heightmap: {path}')
    if image.ndim == 3:
        image = cv2.cvtColor(image,cv2.COLOR_BGRA2GRAY if image.shape[2] == 4 else cv2.COLOR_BGR2GRAY)
    if image.ndim != 2 or min(image.shape) < 2:
        raise ValueError('Heightmap must contain at least 2x2 pixels')
    return image

def prepare(image, spacing=1.0, width_mm=None, max_size=256, smooth=0.0,
            height_scale=0.1, relief=None, crop=None):
    image = np.asarray(image,dtype=np.float64)
    if image.ndim != 2 or min(image.shape) < 2 or not np.isfinite(image).all():
        raise ValueError('Heightmap must be a finite 2D grid of at least 2x2 pixels')
    if not all(math.isfinite(v) for v in (spacing,smooth,height_scale)) or spacing <= 0 or smooth < 0 or height_scale < 0:
        raise ValueError('Spacing must be positive; smoothing and height scale nonnegative')
    if max_size < 2 or width_mm is not None and (not math.isfinite(width_mm) or width_mm <= 0):
        raise ValueError('Maximum grid size must be at least 2 and width positive')
    if relief is not None and (not math.isfinite(relief) or relief < 0):
        raise ValueError('Relief must be finite and nonnegative')
    if crop is not None:
        x,y,w,h = crop
        if min(x,y) < 0 or min(w,h) < 2 or x+w > image.shape[1] or y+h > image.shape[0]:
            raise ValueError('Crop must be inside the image and at least 2x2 pixels')
        image = image[y:y+h,x:x+w]
    original_height,original_width = image.shape
    physical_width = width_mm if width_mm is not None else (original_width-1)*spacing
    physical_depth = physical_width*(original_height-1)/(original_width-1)
    if smooth > 0:
        image = cv2.GaussianBlur(image,(0,0),smooth)
    factor = min(1.0,max_size/max(image.shape))
    if factor < 1:
        shape = (max(2,round(original_width*factor)),max(2,round(original_height*factor)))
        image = cv2.resize(image,shape,interpolation=cv2.INTER_AREA)
    if relief is None:
        elevations = image*height_scale
    else:
        span = float(np.ptp(image))
        elevations = (image-image.min())*relief/span if span else np.zeros_like(image)
    grid_spacing = (physical_width/(image.shape[1]-1),physical_depth/(image.shape[0]-1))
    return elevations,grid_spacing
