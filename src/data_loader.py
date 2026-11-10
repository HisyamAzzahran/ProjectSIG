"""Read supplied inputs and recover original KNIME Arrow caches without executing code."""
from pathlib import Path
import hashlib
import json
import zipfile
import geopandas as gpd
import numpy as np
import pyarrow.ipc as ipc
import shapely

ROOT = Path(__file__).resolve().parents[1]


def cached_table(node, root=ROOT):
    archive = next((root / 'original').glob('Case10*.knwf'))
    with zipfile.ZipFile(archive) as z:
        member = next(n for n in z.namelist() if n.endswith(f'/{node}/port_1/data.zip'))
        # Despite its name data.zip is an Arrow IPC file, not an inner ZIP.
        import pyarrow as pa
        frame = ipc.open_file(pa.BufferReader(z.read(member))).read_all().to_pandas()
        # A KNIME session registers custom Arrow/Pandas logical dtypes. Normalize
        # scalar columns before pivot/groupby, which these dtypes do not support.
        import pandas as pd
        for column in frame.columns:
            if column != 'geometry':
                frame[column] = pd.Series(frame[column].tolist(), index=frame.index)
        return frame


def safe_extract(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            target = (destination / item.filename).resolve()
            if not target.is_relative_to(destination):
                raise ValueError(f'Unsafe archive member: {item.filename}')
        z.extractall(destination)


def load_data(root=ROOT):
    raw = root / 'original/inputs'
    zones, points, roads = [gpd.read_file(raw / f'{n}.zip') for n in ('tract', 'trtpt', 'road')]
    for frame, kind in [(zones, 'Polygon'), (points, 'Point'), (roads, 'LineString')]:
        if frame.crs is None or frame.crs.to_epsg() != 3857:
            raise ValueError('Expected supplied EPSG:3857 geometry; review units before continuing')
        if not frame.geometry.is_valid.all() or frame.geometry.is_empty.any():
            raise ValueError('Invalid or empty input geometry')
        if not frame.geom_type.eq(kind).all():
            raise ValueError(f'Expected {kind}')
    if len(zones) != 136 or len(points) != 136 or not points.ORIG_FID.is_unique:
        raise ValueError('Zone count or centroid identifiers differ from audited data')
    points = points.sort_values('ORIG_FID').reset_index(drop=True)
    if not np.array_equal(points.ORIG_FID, np.arange(1, 137)):
        raise ValueError('Unexpected centroid ordering')
    # TRACT0_ID is a radial transect label, NOT a primary key (126 zeros).
    # Derive polygon IDs from unambiguous point-in-polygon correspondence.
    matches = []
    for polygon in zones.geometry:
        found = points.loc[points.geometry.map(polygon.covers), 'ORIG_FID']
        if len(found) != 1:
            raise ValueError('Polygon must contain exactly one supplied centroid')
        matches.append(int(found.iloc[0]))
    zones['zone_id'] = matches
    zones = zones.sort_values('zone_id').reset_index(drop=True)
    points['zone_id'] = points.ORIG_FID.astype(int)
    for field in ['AREA', 'PERIMETER', 'BEMP_Unif', 'BEMP_CBD', 'TRACT0_ID']:
        if not np.allclose(zones[field], points[field]):
            raise ValueError(f'Polygon/centroid attribute mismatch: {field}')
    # The supplied road SHP omits speed. Recover it from the SAME original
    # workflow's cached reader, after key and geometry identity checks.
    cached = cached_table('GeoFile Reader (#2)', root).set_index('ROAD0_')
    if not roads.ROAD0_.is_unique or set(roads.ROAD0_) != set(cached.index):
        raise ValueError('Road cache key mismatch')
    for row in roads.itertuples():
        value = cached.loc[row.ROAD0_, 'geometry']
        # KNIME registers an Arrow decoder yielding GeoValue; ordinary Python
        # sees the identical storage as a {'0': WKB, '1': CRS} struct.
        wkb = value['0'] if isinstance(value, dict) else value.wkb
        original = shapely.from_wkb(wkb)
        if not original.equals_exact(row.geometry, 1e-6):
            raise ValueError('Road geometry differs from embedded original')
    roads['speed'] = roads.ROAD0_.map(cached.speed).astype(float)
    roads['speed1'] = roads.ROAD0_.map(cached.speed1).astype(float)
    roads['length_m'] = roads.length
    return zones, points, roads


def audit(root=ROOT):
    zones, points, roads = load_data(root)
    report = {}
    for name, frame in [('tract', zones), ('trtpt', points), ('road', roads)]:
        report[name] = dict(count=len(frame), fields=list(frame.columns), crs=str(frame.crs),
                            geometry_types=frame.geom_type.value_counts().to_dict(),
                            invalid=int((~frame.is_valid).sum()),
                            missing=frame.isna().sum().astype(int).to_dict(),
                            bounds=frame.total_bounds.tolist())
    report['TRACT0_ID_zero_count'] = int((points.TRACT0_ID == 0).sum())
    report['cbd_zone_id'] = int(points.loc[points.BEMP_CBD.idxmax(), 'zone_id'])
    report['basic_employment_total'] = float(points.BEMP_Unif.sum())
    report['hashes'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (root/'original').rglob('*') if p.is_file()}
    (root/'docs/data_audit.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    return report
