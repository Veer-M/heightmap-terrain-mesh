from collections import Counter
import numpy as np
import pytest
from stl import mesh
from terrain import build_terrain

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
