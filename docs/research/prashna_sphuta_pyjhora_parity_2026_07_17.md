# Prashna Gulika/Sphuta PyJHora Parity

## Scope

One public synthetic daytime chart: Beijing, 1990-01-01 12:00, UTC+8,
Lahiri, Mean Node. PyJHora 4.8.7 is used only as an AGPL external black-box
benchmark.

## Result

| Point | Local | PyJHora | Absolute delta |
|---|---:|---:|---:|
| Gulika | 22.154273° | 21.867466° | 0.286807° |
| Tri Sphuta | 315.345416° | 315.052227° | 0.293189° |
| Chatur Sphuta | 212.102430° | 211.811742° | 0.290688° |
| Pancha Sphuta | 146.837653° | 146.543676° | 0.293977° |

All rows pass the declared 0.5° tolerance. The local Gulika method now uses
the start of Saturn's share in eight equal day/night parts. The historical
Ghatika-end variant remains available as `legacy_ghatika_end`.

## Boundary

This closes one daytime synthetic comparison only. Night charts, all weekdays,
high-latitude sunrise behavior, and additional locations remain untested. No
Prashna verdict, health claim, or production tuning is unlocked by this packet.
