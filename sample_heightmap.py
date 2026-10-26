import cv2
import numpy as np
y,x = np.mgrid[-1:1:48j,-1:1:64j]
image = (255*np.exp(-4*(x*x+y*y))).astype(np.uint8)
if not cv2.imwrite('heightmap.png',image):
    raise OSError('Cannot save heightmap.png')
print('Wrote a 64x48 sample heightmap')
