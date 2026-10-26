from collections import Counter
import numpy as np
import pytest
from stl import mesh
from terrain import build_terrain
from heightfield import load_heightmap, prepare
from mesh_checks import inspect_mesh

def test_closed_oriented_mesh_and_volume(tmp_path):
    result = build_terrain(np.array([[0,10,20],[10,20,30]],dtype=np.uint8))
    edges = Counter()
    directed = Counter()
    for face in result.vectors:
        for i in range(3):
            a,b = tuple(face[i]),tuple(face[(i+1)%3])
            edges[tuple(sorted((a,b)))] += 1
            directed[(a,b)] += 1
    assert all(count == 2 for count in edges.values())
    assert all(directed[(b,a)] == n for (a,b),n in directed.items())
    assert result.get_mass_properties()[0] > 0
    output = tmp_path/'terrain.stl'
    result.save(str(output))
    assert len(mesh.Mesh.from_file(str(output)).vectors) == len(result.vectors)

def test_flat_block():
    result = build_terrain(np.zeros((2,2),dtype=np.uint8))
    assert result.get_mass_properties()[0] == pytest.approx(5)

def test_resize_preserves_physical_bounds():
    elevations,spacing = prepare(np.zeros((101,201)),width_mm=100,max_size=20,relief=10)
    assert max(elevations.shape) == 20
    report = inspect_mesh(build_terrain(elevations,spacing,1,-3))
    assert report['watertight']
    assert report['bounds_mm']['size'] == pytest.approx([100,50,3])
    assert report['signed_volume_mm3'] == pytest.approx(15000,rel=1e-6)

def test_sixteen_bit_input_and_normalization(tmp_path):
    import cv2
    image = np.array([[0,65535],[32000,1000]],dtype=np.uint16)
    path = tmp_path/'heights.png'
    assert cv2.imwrite(str(path),image)
    loaded = load_heightmap(path)
    assert loaded.dtype == np.uint16
    elevations,_ = prepare(loaded,relief=20)
    assert elevations.min() == 0
    assert elevations.max() == pytest.approx(20)

def test_crop_and_smoothing():
    image = np.zeros((20,30))
    image[10,15] = 255
    raw,_ = prepare(image,crop=(5,5,20,10))
    smoothed,_ = prepare(image,crop=(5,5,20,10),smooth=2)
    assert raw.shape == (10,20)
    assert smoothed.max() < raw.max()
    with pytest.raises(ValueError):
        prepare(image,crop=(29,0,3,3))

def test_report_detects_open_and_reversed_faces():
    model = build_terrain(np.zeros((2,2)))
    report = inspect_mesh(model)
    assert report['watertight']
    assert report['surface_area_mm2'] == pytest.approx(22)
    opened = mesh.Mesh(model.data[:-1].copy())
    assert inspect_mesh(opened)['boundary_edges'] == 3
    model.vectors[0] = model.vectors[0][::-1]
    assert inspect_mesh(model)['inconsistent_edges'] == 3

@pytest.mark.parametrize('options',[{'max_size':1},{'spacing':0},{'smooth':-1},{'relief':float('nan')}])
def test_bad_preparation_options(options):
    with pytest.raises(ValueError):
        prepare(np.zeros((3,3)),**options)
