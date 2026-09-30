"""Recover full rides for the compressed original sample; requires numpy."""
import base64
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent

def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2))

def main():
    original = json.loads((ROOT / 'original_pickups.json').read_text())
    points = np.frombuffer(base64.b64decode(original['b64']), dtype='<u2').reshape(-1, 3)
    rides = json.loads((ROOT / 'rides_2015-01-15_0800_0900.json').read_text())
    by_second = defaultdict(list)
    for i, ride in enumerate(rides):
        t = datetime.fromisoformat(ride['pickup_datetime'])
        by_second[t.minute * 60 + t.second].append(i)
    ll = np.array([[float(r['pickup_longitude']), float(r['pickup_latitude'])] for r in rides])
    counts = Counter(points[:, 2])
    pairs = [(j, by_second[int(p[2])][0]) for j, p in enumerate(points)
             if counts[p[2]] == 1 and len(by_second[int(p[2])]) == 1]

    def fit(pairs):
        return np.array([np.polyfit(ll[[i for j, i in pairs], axis],
                                   points[[j for j, i in pairs], axis], 1)
                         for axis in range(2)])

    affine = fit(pairs)
    def candidates(tolerance):
        predicted = ll * affine[:, 0] + affine[:, 1]
        return [[i for i in by_second[int(p[2])]
                 if np.max(np.abs(predicted[i] - p[:2])) < tolerance] for p in points]

    for _ in range(2):
        options = candidates(1.5)
        affine = fit([(j, v[0]) for j, v in enumerate(options) if len(v) == 1])
    options = candidates(0.51)  # half a quantization unit plus fitted-transform error
    assert all(options), 'Unmatched original pickup'
    groups = defaultdict(list)
    for j, choices in enumerate(options):
        groups[tuple(choices)].append(j)
    assigned = {}
    for choices, indices in groups.items():
        assert len(choices) == len(indices), 'Ambiguous group cardinality'
        if len(choices) > 1:
            assert len({tuple(points[j]) for j in indices}) == 1
            assert len({tuple(ll[i]) for i in choices}) == 1
        for j, i in zip(sorted(indices), sorted(choices)):
            assigned[j] = i
    assert len(set(assigned.values())) == len(points)

    matched, clean, rejected = [], [], []
    for j, point in enumerate(points):
        i = assigned[j]
        ride = dict(rides[i])
        flags = []
        for endpoint in ['pickup', 'dropoff']:
            lon, lat = (float(ride[endpoint + '_' + suffix]) for suffix in ['longitude', 'latitude'])
            if not np.isfinite([lon, lat]).all() or lon == 0 or lat == 0 or not (-180 <= lon <= 180 and -90 <= lat <= 90):
                flags.append(endpoint + '_invalid_coordinates')
        duration = (datetime.fromisoformat(ride['dropoff_datetime']) - datetime.fromisoformat(ride['pickup_datetime'])).total_seconds()
        if duration <= 0:
            flags.append('nonpositive_duration')
        drop_ll = np.array([float(ride['dropoff_longitude']), float(ride['dropoff_latitude'])])
        drop_xy = (drop_ll * affine[:, 0] + affine[:, 1]) * [original['W'] / 65535, original['H'] / 65535]
        ride.update(original_pickup_index=j, source_row_index=i,
                    pickup_seconds_after_0800=int(point[2]),
                    pickup_xy_km=(point[:2] * [original['W'] / 65535, original['H'] / 65535]).tolist(),
                    dropoff_xy_km=drop_xy.tolist() if 'dropoff_invalid_coordinates' not in flags else None,
                    duration_seconds=duration, quality_flags=flags,
                    equivalent_pickup_group=options[j] if len(options[j]) > 1 else None)
        matched.append(ride)
        (rejected if flags else clean).append(ride)
    short = [r for r in clean if r['pickup_seconds_after_0800'] < 900]
    report = dict(source_records=len(rides), original_hour_pickups=len(points),
                  matched_hour_pickups=len(matched), clean_hour_rides=len(clean),
                  rejected_hour_rides=len(rejected),
                  original_first15_pickups=int(sum(points[:, 2] < 900)), clean_first15_rides=len(short),
                  rejected_first15_rides=sum(r['pickup_seconds_after_0800'] < 900 for r in rejected),
                  rejection_reason_counts=dict(Counter(f for r in rejected for f in r['quality_flags'])),
                  equivalent_pickup_groups=sum(len(v) > 1 for v in groups.values()),
                  affine_lonlat_to_quantized_xy=affine.tolist(),
                  matching_tolerance_quantization_units=0.51,
                  geographic_filter='Original sample membership; no filtering of destination borough',
                  cleaning='Nonzero finite geographic coordinates within global bounds; positive trip duration')
    save('matched_manhattan_hour.json', matched)
    save('clean_manhattan_hour.json', clean)
    save('clean_manhattan_first15.json', short)
    save('rejected_manhattan_hour.json', rejected)
    save('matching_report.json', report)
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
