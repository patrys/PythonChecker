import json
import sys


def main(filename, path):
    from checker import get_problems
    with open(filename, 'rb') as f:
        source = f.read()
    if sys.version_info[0] >= 3:
        source = source.decode('utf-8')
    problems = get_problems(source, path)
    json.dump(problems, sys.stdout)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        print('Usage: %s %s <filename> <path>' % (sys.executable, sys.argv[0]))
