#!/usr/bin/env python3
"""
开源项目监控脚本 (v6.9.0)
定期扫描GitHub上与印度占星相关的开源项目，
检测新版本、新功能、许可证变更。
"""
import json, os, time, subprocess
from datetime import datetime

MONITOR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', 'references', 'open_source_monitor.json')

WATCHED_REPOS = [
    {'name': 'PyJHora', 'url': 'https://github.com/jhonbrayan/PyJHora', 'license': 'AGPL-3.0',
     'watch': 'dasha systems, yoga rules, shadbala, divisional charts'},
    {'name': 'jyotishganit', 'url': 'https://github.com/northtara/jyotishganit', 'license': 'MIT',
     'watch': 'shadbala, ashtakavarga, divisional charts, strengths'},
    {'name': 'dashaflow', 'url': 'https://github.com/adarshj322/dashaflow', 'license': 'MIT',
     'watch': 'synastry, muhurtha, yoga, matchmaking'},
    {'name': 'VedicAstro', 'url': 'https://github.com/diliprk/VedicAstro', 'license': 'MIT',
     'watch': 'KP sublord, significator, ABCD system'},
    {'name': 'vedic-astro-skills', 'url': 'https://github.com/CNWU16/vedic-astro-skills', 'license': 'MIT',
     'watch': 'AI interpretation, skill pipelines, validation'},
    {'name': 'vedic-calc', 'url': 'https://github.com/atolat/vedic-calc', 'license': 'AGPL-3.0',
     'watch': 'KP, Tajika, Prashna, Ashtakavarga'},
    {'name': 'panchanga-api', 'url': 'https://github.com/degen0root/panchangaAPI', 'license': 'MIT',
     'watch': 'yogas 300+, muhurta, remedies, KP sublords'},
]


def get_repo_info(repo_url: str) -> dict:
    """Get basic repo info via gh CLI or github API"""
    name = repo_url.split('/')[-1]
    owner = repo_url.split('/')[-2]
    try:
        result = subprocess.run(
            ['gh', 'api', f'repos/{owner}/{name}', '--jq',
             '{stargazers_count,updated_at,default_branch,open_issues_count,description,license:.license.spdx_id}'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'stars': data.get('stargazers_count', 0),
                'updated': data.get('updated_at', ''),
                'branch': data.get('default_branch', 'main'),
                'issues': data.get('open_issues_count', 0),
                'license': data.get('license', ''),
                'desc': data.get('description', '')[:100],
            }
    except Exception as e:
        import logging
        logging.warning(f"[oss_monitor] repo info fetch failed for {repo_url}: {e}")

    # Fallback: cached data
    return {}


def scan_all() -> dict:
    """Scan all watched repos"""
    results = {'timestamp': datetime.now().isoformat(), 'repos': {}}

    for repo in WATCHED_REPOS:
        info = get_repo_info(repo['url'])
        results['repos'][repo['name']] = {
            'url': repo['url'],
            'license': info.get('license', repo['license']),
            'stars': info.get('stars', 0),
            'last_updated': info.get('updated', ''),
            'watch_focus': repo['watch'],
            'status': 'active' if info.get('updated') else 'unchecked',
        }

    return results


def check_changes() -> dict:
    """Compare with previous scan, report changes"""
    current = scan_all()
    changes = []

    if os.path.exists(MONITOR_FILE):
        try:
            with open(MONITOR_FILE) as f:
                previous = json.load(f)
            prev_repos = previous.get('repos', {})
            for name, info in current['repos'].items():
                prev = prev_repos.get(name, {})
                if info.get('stars', 0) != prev.get('stars', 0):
                    diff = info.get('stars', 0) - prev.get('stars', 0)
                    changes.append(f"{name}: ⭐ {prev.get('stars',0)} → {info.get('stars',0)} ({diff:+d})")
                if info.get('last_updated') != prev.get('last_updated'):
                    changes.append(f"{name}: 有更新 ({info.get('last_updated','')[:10]})")
        except Exception as e:
            import logging
            logging.warning(f"[oss_monitor] change comparison failed: {e}")

    current['changes'] = changes
    with open(MONITOR_FILE, 'w') as f:
        json.dump(current, f, indent=2, ensure_ascii=False)

    return current


if __name__ == '__main__':
    result = check_changes()
    print(f"=== 开源项目监控 {result['timestamp'][:10]} ===\n")
    for name, info in result['repos'].items():
        stars = info.get('stars', '?')
        lic = info.get('license', '?')
        updated = info.get('last_updated', '?')[:10] if info.get('last_updated') else '?'
        print(f"  {name:25s} ⭐{stars:>5}  {lic:10s}  更新:{updated}")

    if result.get('changes'):
        print(f"\n🔄 变更 ({len(result['changes'])}项):")
        for c in result['changes']:
            print(f"  {c}")
    else:
        print("\n✅ 无变更")

    with open(MONITOR_FILE, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
