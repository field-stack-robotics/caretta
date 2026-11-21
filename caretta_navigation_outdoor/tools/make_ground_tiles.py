#!/usr/bin/env python3
"""Cut the top-down image of the Gazebo world into map tiles for RViz (rviz_satellite, file://).

RViz draws the tiles with "Draw Behind", so costmaps, plans and the robot stay on top (a textured
Marker was drawn over the half-transparent costmaps). Run again if the world or its image changes:
  python3 tools/make_ground_tiles.py media/outdoor_ground.jpg media/ground_tiles
Image: rendered from a camera 240 m above caretta_outdoor.sdf, north up, covering x -10..40 m,
y -10..30 m (map = Gazebo world, origin = lat 52.0, lon 5.0). Outside the image: plain grass.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

LAT0, LON0 = 52.0, 5.0              # map origin (navsat_transform datum)
X0, X1, Y0, Y1 = -10.0, 40.0, -10.0, 30.0   # area of the image in the map, m
ZOOM, BLOCKS, TILE = 21, 3, 256      # 7 x 7 tiles of about 11.8 m around the origin
GRASS = (147, 185, 126)
# metres per degree at the origin (WGS84), enough over a few hundred metres
M_LAT = 111132.92 - 559.82 * math.cos(2 * math.radians(LAT0)) + 1.175 * math.cos(4 * math.radians(LAT0))
M_LON = 111412.84 * math.cos(math.radians(LAT0)) - 93.5 * math.cos(3 * math.radians(LAT0))


def tile_of(lat, lon, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return int(x), int(y)


def main(src, out):
    img = np.asarray(Image.open(src).convert('RGB'))
    h, w, _ = img.shape
    n = 2 ** ZOOM
    cx, cy = tile_of(LAT0, LON0, ZOOM)
    for tx in range(cx - BLOCKS, cx + BLOCKS + 1):
        for ty in range(cy - BLOCKS, cy + BLOCKS + 1):
            # lat/lon of every pixel centre of this tile (Web Mercator)
            px = (tx + (np.arange(TILE) + 0.5) / TILE)[None, :].repeat(TILE, 0)
            py = (ty + (np.arange(TILE) + 0.5) / TILE)[:, None].repeat(TILE, 1)
            lon = px / n * 360.0 - 180.0
            lat = np.degrees(np.arctan(np.sinh(np.pi * (1.0 - 2.0 * py / n))))
            x = (lon - LON0) * M_LON
            y = (lat - LAT0) * M_LAT
            u = ((x - X0) / (X1 - X0) * w).astype(int)
            v = ((Y1 - y) / (Y1 - Y0) * h).astype(int)
            inside = (u >= 0) & (u < w) & (v >= 0) & (v < h)
            tile = np.empty((TILE, TILE, 3), np.uint8)
            tile[:] = GRASS
            tile[inside] = img[v[inside], u[inside]]
            path = os.path.join(out, str(ZOOM), str(tx))
            os.makedirs(path, exist_ok=True)
            Image.fromarray(tile).save(os.path.join(path, f'{ty}.jpg'), quality=85)
    print(f'{(2 * BLOCKS + 1) ** 2} tiles, zoom {ZOOM}, centre tile {cx}/{cy} -> {out}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
