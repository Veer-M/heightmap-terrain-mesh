import numpy as np

def inspect_mesh(model):
    triangles = np.asarray(model.vectors,dtype=np.float64)
    if not len(triangles) or not np.isfinite(triangles).all():
        raise ValueError('Mesh must contain finite triangles')
    vertices,inverse = np.unique(triangles.reshape(-1,3),axis=0,return_inverse=True)
    ids = inverse.reshape(-1,3)
    directed = np.concatenate([ids[:,[0,1]],ids[:,[1,2]],ids[:,[2,0]]])
    edges = np.sort(directed,axis=1)
    unique_edges,edge_ids,counts = np.unique(edges,axis=0,return_inverse=True,return_counts=True)
    direction = np.where(directed[:,0] < directed[:,1],1,-1)
    balance = np.bincount(edge_ids,weights=direction,minlength=len(unique_edges))
    area_twice = np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)
    degenerate = int(np.sum(area_twice <= 1e-12))
    boundary = int(np.sum(counts == 1))
    nonmanifold = int(np.sum(counts > 2))
    winding = int(np.sum((counts == 2)&(balance != 0)))
    signed_volume = float(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6)
    lower,upper = vertices.min(axis=0),vertices.max(axis=0)
    return {'triangles':len(triangles),'vertices':len(vertices),'edges':len(unique_edges),
            'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'inconsistent_edges':winding,
            'degenerate_triangles':degenerate,
            'watertight':not (boundary or nonmanifold or winding or degenerate),
            'signed_volume_mm3':signed_volume,'surface_area_mm2':float(area_twice.sum()/2),
            'bounds_mm':{'min':lower.tolist(),'max':upper.tolist(),'size':(upper-lower).tolist()}}

def preview(elevations, spacing, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    height,width = elevations.shape
    x,y = np.meshgrid(np.arange(width)*spacing[0],np.arange(height)*spacing[1])
    figure = plt.figure(figsize=(10,6))
    axes = figure.add_subplot(111,projection='3d')
    axes.plot_surface(x,y,elevations,cmap='terrain',rcount=100,ccount=100,linewidth=0,antialiased=True)
    axes.set(xlabel='X (mm)',ylabel='Y (mm)',zlabel='Elevation (mm)',title='Prepared terrain surface')
    axes.set_box_aspect((max(x.max(),1),max(y.max(),1),max(float(np.ptp(elevations)),1)))
    figure.tight_layout()
    figure.savefig(output,dpi=150)
    plt.close(figure)
