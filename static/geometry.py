"""Exact geometry for the static protocol: Voronoi cells clipped to the city, loads, neighbours, compactness, splitting.

Everything here is computed from centres and requests; nothing is estimated.
"""
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union
from shapely import prepared

TOL = 1e-9


def load_city(path):
    import json
    d = json.load(open(path))
    rings = d["rings"]
    poly = Polygon(rings[0], rings[1:])
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def load_requests(path):
    import json
    d = json.load(open(path))
    q = np.array(d["quantized"], float)
    return np.c_[q[:, 0] / 65535 * d["W_km"], q[:, 1] / 65535 * d["H_km"]]


def halfplane_cell(i, centres, bbox_poly):
    """Voronoi cell of centre i among all centres, clipped to bbox_poly, by half-plane clipping.

    Cheap when only a few cells are needed: O(n) clips per cell."""
    c = centres[i]
    cell = bbox_poly
    d2 = ((centres - c) ** 2).sum(1)
    order = np.argsort(d2)
    for j in order[1:]:
        if cell.is_empty:
            break
        cj = centres[j]
        m = (c + cj) / 2
        n = cj - c
        nn = np.hypot(*n)
        if nn < TOL:
            continue
        n = n / nn
        # half-plane {x : (x - m).n <= 0}; clip by a big polygon on that side
        t = np.array([-n[1], n[0]])
        L = 1e3
        hp = Polygon([m + t * L, m - t * L, m - t * L - n * L, m + t * L - n * L])
        cell = cell.intersection(hp)
    return cell


def all_cells(centres, city):
    """Voronoi cells of all centres clipped to the city. Uses scipy for the diagram and shapely for clipping."""
    from scipy.spatial import Voronoi
    n = len(centres)
    minx, miny, maxx, maxy = city.bounds
    pad = 10 * max(maxx - minx, maxy - miny)
    # add far-away mirror points so that every real cell is bounded
    far = np.array([[minx - pad, miny - pad], [maxx + pad, miny - pad], [maxx + pad, maxy + pad], [minx - pad, maxy + pad]])
    pts = np.vstack([centres, far])
    vor = Voronoi(pts)
    cells = []
    for i in range(n):
        reg = vor.regions[vor.point_region[i]]
        if -1 in reg or len(reg) == 0:
            cells.append(halfplane_cell(i, centres, city))
            continue
        poly = Polygon(vor.vertices[reg])
        cells.append(poly.intersection(city))
    return cells


def loads(cells, requests, prepared_cells=None):
    """Number of requests in each cell. A request on a shared edge is counted once, for the lowest index."""
    n = len(cells)
    owner = np.full(len(requests), -1)
    pts = [Point(p) for p in requests]
    for i, cell in enumerate(cells):
        if cell.is_empty:
            continue
        pc = prepared.prep(cell)
        for k, pt in enumerate(pts):
            if owner[k] < 0 and pc.intersects(pt):
                owner[k] = i
    counts = np.bincount(owner[owner >= 0], minlength=n)
    return counts, owner


def nearest_owner(centres, requests):
    """Owner by nearest centre: exact for Voronoi cells and fast."""
    from scipy.spatial import cKDTree
    t = cKDTree(centres)
    _, idx = t.query(requests)
    return idx


def neighbours(cells, n):
    """Pairs sharing an edge of positive length."""
    nb = [set() for _ in range(n)]
    for i in range(n):
        if cells[i].is_empty:
            continue
        for j in range(i + 1, n):
            if cells[j].is_empty:
                continue
            if not cells[i].intersects(cells[j]):
                continue
            inter = cells[i].boundary.intersection(cells[j].boundary)
            if inter.length > TOL:
                nb[i].add(j)
                nb[j].add(i)
    return nb


def width_and_diameter(poly):
    """Diameter and minimum width of a convex polygon (or the convex hull of a clipped cell)."""
    if poly.is_empty:
        return 0.0, 0.0
    hull = poly.convex_hull
    pts = np.array(hull.exterior.coords)[:-1]
    m = len(pts)
    if m < 3:
        return 0.0, 0.0
    # diameter
    d2 = ((pts[:, None, :] - pts[None, :, :]) ** 2).sum(2)
    diam = np.sqrt(d2.max())
    # width: min over edge directions of the extent perpendicular to the edge
    w = np.inf
    for k in range(m):
        e = pts[(k + 1) % m] - pts[k]
        L = np.hypot(*e)
        if L < TOL:
            continue
        nrm = np.array([-e[1], e[0]]) / L
        proj = pts @ nrm
        w = min(w, proj.max() - proj.min())
    return diam, w


def compact(poly, ratio=2.0):
    d, w = width_and_diameter(poly)
    return w > TOL and d / w <= ratio + 1e-9


def split_cell(poly):
    """Cut a convex cell into two halves of equal area by a line perpendicular to its long axis; return the two centroids."""
    hull = poly.convex_hull
    pts = np.array(hull.exterior.coords)[:-1]
    # area centroid and covariance of the polygon (uniform density)
    c = np.array(hull.centroid.coords[0])
    # covariance by triangulation from the centroid
    cov = np.zeros((2, 2)); A = 0.0
    for k in range(len(pts)):
        a, b = pts[k], pts[(k + 1) % len(pts)]
        tri_area = 0.5 * abs((a[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (a[1] - c[1]))
        if tri_area < 1e-15:
            continue
        # covariance of a uniform triangle about the polygon centroid
        v = np.array([c, a, b]) - c
        tc = v.mean(0)
        cov_tri = (v.T @ v) / 12 + np.outer(tc, tc)  # about polygon centroid
        cov += tri_area * cov_tri; A += tri_area
    cov /= max(A, 1e-15)
    vals, vecs = np.linalg.eigh(cov)
    u = vecs[:, np.argmax(vals)]
    if abs(vals[0] - vals[1]) < 1e-12:
        u = np.array([1.0, 0.0])
    # find t with area(hull ∩ {u.x <= t}) = A/2 by bisection on the sorted projections (exact enough: 1e-12 km)
    proj = pts @ u
    lo, hi = proj.min(), proj.max()
    total = hull.area

    def half(t):
        n = u; m = c + (t - c @ u) * u
        tt = np.array([-n[1], n[0]]); L = 1e3
        hp = Polygon([m + tt * L, m - tt * L, m - tt * L - n * L, m + tt * L - n * L])
        return hull.intersection(hp)

    for _ in range(80):
        mid = (lo + hi) / 2
        if half(mid).area < total / 2:
            lo = mid
        else:
            hi = mid
    t = (lo + hi) / 2
    hm = half(t)
    hp = hull.difference(hm)
    return np.array(hm.centroid.coords[0]), np.array(hp.centroid.coords[0])
