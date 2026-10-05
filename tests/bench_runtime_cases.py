"""Same behavioral cases under CPython and MicroPython Unix, with mock GPIO.

Invoked by tools/check-bench-runtime.py in a disposable working directory.
Does not test physical GPIO, timing accuracy, RP2040 flash or optical output.
"""
import json
import os
import sys
import time

source = open(sys.argv[1]).read()
original_patterns = open(sys.argv[2]).read()
os.chdir(sys.argv[3])


class Pin:
    def __init__(self, number):
        self.number = number


class PWM:
    instances = []
    fail_pin = None

    def __init__(self, pin, freq, duty_u16):
        assert freq == 2000 and duty_u16 == 0
        self.pin = pin.number
        self.duty = duty_u16
        self.instances.append(self)

    def duty_u16(self, duty):
        if self.pin == self.fail_pin and duty != 0:
            PWM.fail_pin = None
            raise OSError('Injected GPIO failure')
        assert 0 <= duty <= 65535
        self.duty = duty


class Machine:
    pass


Machine.Pin = Pin
Machine.PWM = PWM
sys.modules['machine'] = Machine
saved_rename = os.rename
# No physical waits or disk-wide sync needed for behavioral tests.
mock_time = Machine()
mock_time.sleep = lambda seconds: None
mock_os = Machine()
mock_os.rename = saved_rename
mock_os.sync = lambda: None
sys.modules['time'] = mock_time
sys.modules['os'] = mock_os


def put(name, text):
    with open(name, 'w') as f:
        f.write(text)


def values():
    return [p.duty for p in PWM.instances]


def boot(state=None, patterns=None):
    for name in ['bench-state.json', 'bench-state.tmp']:
        try:
            os.remove(name)
        except OSError:
            pass
    if state is not None:
        put('bench-state.json', state)
    put('patterns.json', original_patterns if patterns is None else patterns)
    PWM.instances = []
    PWM.fail_pin = None
    namespace = {'__name__': 'main'}
    exec(source, namespace)
    assert [p.pin for p in PWM.instances] == list(range(10))
    return namespace


def rejects(fn):
    try:
        fn()
    except (ValueError, OSError):
        return
    raise AssertionError('Expected rejection')


def first_boot():
    boot()
    assert values() == [0] * 10


def channels_and_dimming():
    m = boot()
    for i in range(10):
        m['show']('walk-' + str(i), 1, False)
        expected = [0] * 10
        expected[i] = 65535
        assert values() == expected
    for scale in [0, 0.1, 0.3, 1]:
        m['show']('vancouver', scale, False)
        assert values() == [round(v / 255 * scale * 65535)
                            for v in m['patterns']['vancouver']]


def invalid_requests_do_not_mutate():
    m = boot()
    m['show']('all', 0.3, False)
    before = values()
    for bad in [-1, 1.01, True, None, '0.1', float('nan'), float('inf')]:
        rejects(lambda: m['show']('all', bad, False))
        assert values() == before
    for name in ['unknown', [], None]:
        rejects(lambda: m['show'](name, 0.1, False))
        assert values() == before
    for frame in [[255], [255] * 11, [256] * 10, [True] * 10, [1.5] * 10]:
        m['patterns']['bad'] = frame
        rejects(lambda: m['show']('bad', 0.1, False))
        assert values() == before


def persistence_and_restore():
    m = boot()
    m['show']('seattle', 0.3)
    expected = values()
    saved = open('bench-state.json').read()
    m = boot(saved)
    assert values() == expected
    m['show']('off', 0)
    boot(open('bench-state.json').read())
    assert values() == [0] * 10


def corrupt_state_fails_dark():
    for state in ['{', '[]', 'null', '{}', '{"name": [], "brightness": 1}',
                  '{"name":"all","brightness":true}',
                  '{"name":"all","brightness":"0.1"}',
                  '{"name":"missing","brightness":1}',
                  '{"name":"all","brightness":2}']:
        boot(state)
        assert values() == [0] * 10


def corrupt_patterns_fail_dark():
    for patterns in ['{', '[]', '{"off":[0]}', '{"off":[255,0,0,0,0,0,0,0,0,0]}']:
        rejects(lambda: boot(patterns=patterns))
        assert values() == [0] * 10


def interrupted_write_uses_previous_state():
    m = boot()
    m['show']('vancouver', 0.1)
    expected = values()
    saved = open('bench-state.json').read()
    put('bench-state.tmp', '{')
    PWM.instances = []
    namespace = {'__name__': 'main'}
    exec(source, namespace)
    assert values() == expected
    assert open('bench-state.json').read() == saved


def storage_failure_blanks():
    m = boot()
    m['show']('vancouver', 0.1)
    previous = open('bench-state.json').read()

    def failed_rename(a, b):
        raise OSError('Injected rename failure')

    mock_os.rename = failed_rename
    try:
        rejects(lambda: m['show']('all', 1))
        assert values() == [0] * 10
        assert open('bench-state.json').read() == previous
    finally:
        mock_os.rename = saved_rename


def gpio_failure_blanks():
    m = boot()
    PWM.fail_pin = 4
    rejects(lambda: m['show']('all', 1, False))
    assert values() == [0] * 10


def walk_finishes_dark_without_saving():
    m = boot()
    m['show']('vancouver', 0.1)
    saved = open('bench-state.json').read()
    frames = []
    mock_time.sleep = lambda seconds: frames.append(values())
    try:
        m['walk'](1, 1)
    finally:
        mock_time.sleep = lambda seconds: None
    assert len(frames) == 10
    for i, frame in enumerate(frames):
        expected = [0] * 10
        expected[i] = 65535
        assert frame == expected
    assert values() == [0] * 10
    assert open('bench-state.json').read() == saved


def interrupted_walk_finishes_dark():
    m = boot()

    def interrupt(seconds):
        raise KeyboardInterrupt()

    mock_time.sleep = interrupt
    try:
        try:
            m['walk']()
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError('Expected keyboard interrupt')
        assert values() == [0] * 10
    finally:
        mock_time.sleep = lambda seconds: None


cases = [first_boot, channels_and_dimming, invalid_requests_do_not_mutate,
         persistence_and_restore, corrupt_state_fails_dark, corrupt_patterns_fail_dark,
         interrupted_write_uses_previous_state, storage_failure_blanks,
         gpio_failure_blanks, walk_finishes_dark_without_saving,
         interrupted_walk_finishes_dark]
for case in cases:
    case()
    print('PASS', case.__name__)
print('RESULT', json.dumps({'casesPassed': len(cases), 'physicalTested': False}))
