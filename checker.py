import ast
from collections import namedtuple
import sys
import tempfile

try:
    # as plugin
    from .pep8 import pep8
    from .pyflakes import checker
except (SystemError, ValueError):
    # external process
    from pep8 import pep8
    from pyflakes import checker

PEP8_IGNORED = {'E501', 'W191'}

Problem = namedtuple('Problem', 'level lineno offset message')


class Pep8Report(pep8.BaseReport):

    def __init__(self, *args, **kwargs):
        self.problems = []
        if sys.version_info[0] >= 3:
            super().__init__(*args, **kwargs)
        else:
            super(Pep8Report, self).__init__(*args, **kwargs)

    def error(self, line_number, offset, text, check):
        level = 'error' if text.startswith('E') else 'warn'
        self.problems.append(Problem(level, line_number, offset, text))


def get_problems(source, filename):
    flakes = get_flakes(source, filename)
    style_problems = get_style_problems(source, filename)
    return list(flakes) + list(style_problems)


def get_flakes(source, filename):
    try:
        tree = ast.parse(source, filename, "exec")
    except SyntaxError:
        value = sys.exc_info()[1]
        msg = value.args[0]
        yield Problem('error', value.lineno, value.offset, msg)
    else:
        results = checker.Checker(tree, filename)
        for m in results.messages:
            yield Problem('warn', m.lineno, m.col,
                          m.message % m.message_args)


def get_style_problems(source, filename):
    guide = pep8.StyleGuide(reporter=Pep8Report, ignore=PEP8_IGNORED)
    lines = source.splitlines(True)
    checker = pep8.Checker(filename, lines, guide.options)
    checker.check_all()
    return checker.report.problems


def get_external(source, filename, executable):
    import json
    import subprocess
    with tempfile.NamedTemporaryFile() as tf:
        tf.write(source.encode('utf-8'))
        output = subprocess.check_output([executable, __file__, tf.name])
    problems = json.loads(output.decode('utf-8'))
    problems = [Problem(*p) for p in problems]
    return problems


def main(filename):
    import json
    with open(filename, 'rb') as f:
        source = f.read()
    if sys.version_info[0] >= 3:
        source = source.decode('utf-8')
    problems = get_problems(source, filename)
    json.dump(problems, sys.stdout)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print('Usage: %s %s <filename>' % (sys.executable, sys.argv[0],))
