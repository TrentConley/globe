"""Run identical bench cases under CPython and an explicit MicroPython binary."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--micropython', required=True)
args = p.parse_args()
source = ROOT / 'firmware/ten-cell-bench/main.py'
patterns = source.with_name('patterns.json')
results = []
for label, runtime in [('CPython', sys.executable), ('MicroPython Unix', args.micropython)]:
    with tempfile.TemporaryDirectory(prefix='globe-bench-test-') as work:
        command = [runtime, str(ROOT / 'tests/bench_runtime_cases.py'),
                   str(source), str(patterns), work]
        run = subprocess.run(command, capture_output=True, text=True)
        if run.returncode:
            print(run.stdout + run.stderr)
            raise SystemExit(run.returncode)
        cases = [line[5:] for line in run.stdout.splitlines() if line.startswith('PASS ')]
        result = json.loads(next(line[7:] for line in run.stdout.splitlines() if line.startswith('RESULT ')))
        assert len(cases) == result['casesPassed'] == 11
        version = subprocess.check_output([runtime, '-c', 'import sys; print(sys.version)'], text=True).strip()
        results.append({'runtime': label, 'version': version, 'passed': cases})
report = {'revision': 'sample-A1', 'physicalTested': False,
          'scope': 'Runtime behavior with mocked machine.Pin/PWM; host filesystem, no physical Pico or flash power-cut test',
          'firmwareSHA256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'patternsSHA256': hashlib.sha256(patterns.read_bytes()).hexdigest(),
          'microPythonSource': 'https://github.com/micropython/micropython/tree/4ce2dd2cdab6e57f3982fc899f15a2103d71b0be',
          'microPythonBuild': 'Unix standard; SSL, BTREE, FFI, FAT, LFS1, LFS2 and frozen manifest disabled',
          'results': results}
(ROOT / 'engineering/release/sample-firmware-checks.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
