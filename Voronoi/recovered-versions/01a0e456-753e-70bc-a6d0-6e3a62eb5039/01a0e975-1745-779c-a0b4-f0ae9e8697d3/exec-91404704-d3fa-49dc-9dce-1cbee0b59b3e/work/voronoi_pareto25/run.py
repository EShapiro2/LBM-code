import sys,json,signal,time,shutil,math
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import MultiPoint,Polygon,Point
from scipy.optimize import minimize_scalar
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'voronoi_fresh_free25'))
import run as base
