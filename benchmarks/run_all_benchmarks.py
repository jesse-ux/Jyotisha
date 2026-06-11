#!/usr/bin/env python3
"""
统一Benchmark运行器 (v6.9.0)
运行所有已建立的benchmark并生成综合报告。
"""
import sys, os, json, time, subprocess
from datetime import datetime

BENCHMARK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '..', 'benchmarks', 'jyotish', 'scripts')

BENCHMARKS = {
    'chara_dasha': {
        'file': 'run_chara_dasha_knrao.py',
        'name': 'Chara Dasha KN Rao Method',
        'expected': 95.0,
        'unit': '%',
    },
    'vimshottari': {
        'file': 'run_vimshottari_compare.py',
        'name': 'Vimshottari Dasha Comparison',
        'expected': 80.0,
        'unit': '%',
        'note': 'PyJHora约定差异,非算法错误',
    },
    'shadbala': {
        'file': 'run_shadbala_compare.py',
        'name': 'Shadbala Comparison',
        'expected': 85.0,
        'unit': '%',
    },
    'yoga_accuracy': {
        'file': 'run_yoga_accuracy.py',
        'name': 'Yoga Detection Accuracy',
        'expected': 90.0,
        'unit': '%',
    },
}


def run_benchmark(name: str, config: dict) -> dict:
    """运行单个benchmark"""
    filepath = os.path.join(BENCHMARK_DIR, config['file'])
    if not os.path.exists(filepath):
        return {'name': name, 'status': 'SKIP', 'reason': f'File not found: {filepath}'}

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=True, text=True, timeout=120,
            cwd=BENCHMARK_DIR
        )
        elapsed = time.time() - start

        output = result.stdout + result.stderr
        passed = result.returncode == 0

        # 尝试提取通过率
        pass_rate = None
        for line in output.split('\n'):
            if 'PASS' in line and '%' in line:
                try:
                    pass_rate = float(line.split('PASS')[0].strip().split()[-1].replace('%', ''))
                except:
                    pass

        return {
            'name': config['name'],
            'status': 'PASS' if passed else 'FAIL',
            'pass_rate': pass_rate,
            'expected': config['expected'],
            'unit': config['unit'],
            'elapsed': round(elapsed, 2),
            'exit_code': result.returncode,
            'output_summary': output[-200:] if output else 'No output',
        }
    except subprocess.TimeoutExpired:
        return {'name': config['name'], 'status': 'TIMEOUT', 'reason': '>120s'}
    except Exception as e:
        return {'name': config['name'], 'status': 'ERROR', 'reason': str(e)}


def run_all_benchmarks() -> dict:
    """运行所有benchmark并生成报告"""
    results = {}
    total_pass = 0
    total_fail = 0

    for name, config in BENCHMARKS.items():
        print(f"  Running {config['name']}...", end=' ')
        result = run_benchmark(name, config)
        results[name] = result
        status = result['status']
        if status == 'PASS':
            total_pass += 1
            print('PASS')
        elif status == 'FAIL':
            total_fail += 1
            print('FAIL')
        else:
            print(status)

    return {
        'timestamp': datetime.now().isoformat(),
        'total': len(BENCHMARKS),
        'passed': total_pass,
        'failed': total_fail,
        'results': results,
        'summary': f'{total_pass}/{total_pass+total_fail} benchmarks passed',
    }


if __name__ == '__main__':
    print("=== Jyotish Benchmark Runner v6.9.0 ===\n")
    report = run_all_benchmarks()
    print(f"\n{report['summary']}")
    for name, r in report['results'].items():
        status = r['status']
        rate = r.get('pass_rate', 'N/A')
        exp = r.get('expected', 'N/A')
        print(f"  {status:6s} {name}: {rate}% (expected: {exp}%)")
