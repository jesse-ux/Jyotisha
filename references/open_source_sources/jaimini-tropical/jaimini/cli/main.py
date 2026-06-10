"""Jaimini Tropical Astrology CLI.

Usage:
    python -m jaimini.cli.main <date> <time> <timezone> <lat> <lon> [options]

Examples:
    # New China chart (1949-10-01, Beijing)
    python -m jaimini.cli.main "1949-10-01" "15:00:00" "+8" "39°54′25″" "116°23′50″"

    # Simple decimal format
    python -m jaimini.cli.main "2025-01-15" "06:30:00" "+5.5" "28.6139" "77.2090"

    # With options
    python -m jaimini.cli.main "1949-10-01" "15:00:00" "+8" "39.907" "116.397" --name "New China" --dasha-only
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from jaimini.chart.chart import Chart
from jaimini.engine.time_utils import parse_dms, parse_timezone, format_dms, zodiac_position
from jaimini.engine.houses import HOUSE_SYSTEMS
from jaimini.core.karakas import karaka_report
from jaimini.core.dashas import format_dasha_table


def main():
    parser = argparse.ArgumentParser(
        description="Jaimini Tropical Astrology Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m jaimini.cli.main "1949-10-01" "15:00:00" "+8" "39°54′25″" "116°23′50″"
  python -m jaimini.cli.main "2025-01-15" "06:30:00" "+5.5" "28.6139" "77.2090" --dasha-only
        """
    )

    parser.add_argument('date', help='Date in YYYY-MM-DD format')
    parser.add_argument('time', help='Time in HH:MM:SS format')
    parser.add_argument('timezone', help='Timezone offset (e.g., +8, -5:30, +5.5)')
    parser.add_argument('latitude', help='Latitude (decimal or DMS like 39°54′25″N)')
    parser.add_argument('longitude', help='Longitude (decimal or DMS like 116°23′50″E)')

    parser.add_argument('--name', '-n', default='', help='Chart name/label')
    parser.add_argument('--house-system', '-hs', default='W', choices=['W', 'P', 'E'],
                        help='House system: W=Whole Sign, P=Placidus, E=Equal (default: W)')
    parser.add_argument('--include-rahu', '-r', action='store_true',
                        help='Include Rahu in Chara Karaka (8-karaka system)')
    parser.add_argument('--dasha-only', '-d', action='store_true',
                        help='Show only Dasha timeline')
    parser.add_argument('--karakas-only', '-k', action='store_true',
                        help='Show only Karaka assignments')
    parser.add_argument('--output', '-o', help='Save output to file')

    args = parser.parse_args()

    # Parse inputs
    date_str = args.date
    time_str = args.time
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

    lat = parse_dms(args.latitude)
    lon = parse_dms(args.longitude)
    tz = parse_timezone(args.timezone)

    # Build chart
    print(f"\n{'='*60}")
    print(f"  Jaimini Tropical Astrology Engine")
    print(f"  Date: {date_str} {time_str}  |  TZ: UTC{tz:+g}")
    print(f"  Lat: {format_dms(lat)}  |  Lon: {format_dms(lon)}")
    print(f"  House System: {HOUSE_SYSTEMS.get(args.house_system, 'Whole Sign')}")
    if args.name:
        print(f"  Chart: {args.name}")
    print(f"{'='*60}\n")

    chart = Chart(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
        lat, lon, tz, name=args.name, house_system=args.house_system
    )

    # Build output
    output_lines = []

    if args.karakas_only:
        karakas = chart.karakas_8 if args.include_rahu else chart.karakas_7
        output_lines.append(karaka_report(karakas))
        output_lines.append("")
        # Show AK details
        ak = chart.karakas_7[0]
        output_lines.append(f"Atmakaraka: {ak['planet']} at {ak['lon']:.6f}° ({ak['sign']} {ak['degree_in_sign']:.6f}°)")

    elif args.dasha_only:
        output_lines.append(format_dasha_table(chart.chara_dasha, include_antar=True))

    else:
        output_lines.append(chart.summary())

    output = "\n".join(output_lines)
    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\nOutput saved to: {args.output}")


if __name__ == '__main__':
    main()
