Title: Fix AirWatch: zone filtering, normalize coords, meaningful 3D view

Description:
We need to fix and improve the AirWatch section:

- Ensure map points are placed correctly (fix coordinate/order inconsistencies and data normalization).
- Add a zone filter (or global option) so the top indicators (NO2, CO2, PM10, PM2.5, Noise) and predictions can show values for a single zone or globally.
- Add zone filter to the air quality prediction chart; support showing one zone or multiple zones together.
- Replace the current 3D "volumetric" view with an informative visualization (default: aggregated bars per zone, color+height mapping, legend, tooltip).

Implementation notes:
- Backend: support `?zone=<zone_id>` in `/api/airwatch` and `/api/dashboard` (already added). When `zone` is specified, only that zone (or aggregated data) is returned. `zone=global` returns all zones.
- Frontend: added `#zoneSelect` dropdown and logic to request `/api/airwatch?zone=` and refresh indicators and forecast chart.
- Added `Shapely` to `requirements.txt` for future polygon/point-in-polygon filtering if needed.

Next steps (remaining):
- Normalize zone IDs across seeders (`seed_data.py`, `seed_docker.py`) if mismatches exist.
- Rework the 3D view to use `THREE.InstancedMesh` bars with a clear legend and aggregated-by-zone default view.
- Update tests and QA steps.

Labels: enhancement, bug
Assignees: 

