# China location data

`china-locations.json` is a compact runtime snapshot for the profile form. It contains only the country, province, city, district/county names, administrative codes, and centre coordinates required by the product; it intentionally does not include map polygons.

- Source: ChinaGeoJson `info.json`, which republishes DataV.GeoAtlas administrative metadata.
- Upstream license: MIT (ChinaGeoJson, Copyright 2024 ChuXiao).
- Refresh command: `npm run data:china`.

The source snapshot is useful for structured profile selection. It is not a substitute for an address-level geocoder: coordinate precision is administrative-area-centre precision.
