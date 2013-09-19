import ast
from collections import namedtuple
import sys

import sublime
import sublime_plugin

from .pep8 import pep8
from .pyflakes import checker

Problem = namedtuple('Problem', 'level lineno offset message')


class Pep8Report(pep8.BaseReport):

    def __init__(self, *args, **kwargs):
        self.problems = []
        super().__init__(*args, **kwargs)

    def error(self, line_number, offset, text, check):
        self.problems.append(Problem('warn', line_number, offset, text))


class Validator(sublime_plugin.EventListener):

    KNOWN_SYNTAXES = {'Packages/Python/Python.tmLanguage'}
    PEP8_IGNORED = {'E501', 'W191'}

    def __init__(self, *args, **kwargs):
        self.view_cache = {}
        self.view_line = {}
        super().__init__(*args, **kwargs)

    def on_load_async(self, view):
        if view.is_scratch():
            return
        self.revalidate(view)

    def on_post_save_async(self, view):
        if view.is_scratch():
            return
        self.revalidate(view)

    def on_selection_modified_async(self, view):
        if view.is_scratch():
            return
        self.update_statusbar(view)

    def on_pre_close(self, view):
        view_id = view.id()
        if view_id in self.view_line:
            del self.view_line[view_id]
        if view_id in self.view_cache:
            del self.view_cache[view_id]

    def update_statusbar(self, view, force=False):
        line = self.get_selected_line(view)
        view_id = view.id()

        if force or line != self.view_line.get(view.id(), None):
            self.view_line[view_id] = line
            error = self.view_cache.get(view_id, {}).get(line, None)
            if error:
                view.set_status('python-lint-problem', error)
            else:
                view.erase_status('python-lint-problem')

    def get_selected_line(self, view):
        selection = view.sel()
        if not selection:
            return None
        return view.rowcol(selection[0].end())[0]

    def revalidate(self, view):
        if view.settings().get("syntax") not in self.KNOWN_SYNTAXES:
            return
        filename = view.file_name()
        if not filename:
            filename = '<unsaved>'
        source = view.substr(sublime.Region(0, view.size()))
        flakes = self.get_flakes(source, filename)
        style_problems = self.get_style_problems(source, filename)
        problems = list(flakes) + list(style_problems)
        self.highlight_problems(view, problems)
        self.update_statusbar(view, force=True)

    def get_flakes(self, source, filename):
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

    def get_style_problems(self, source, filename):
        guide = pep8.StyleGuide(reporter=Pep8Report, ignore=self.PEP8_IGNORED)
        lines = source.splitlines(True)
        checker = pep8.Checker(filename, lines, guide.options)
        checker.check_all()
        return checker.report.problems

    def highlight_problems(self, view, problems):
        view.erase_regions('python-lint-problem')
        view_id = view.id()
        self.view_cache[view_id] = {}
        regions = []
        for problem in problems:
            self.view_cache[view_id][problem.lineno - 1] = problem.message
            region_start = view.text_point(problem.lineno - 1, problem.offset)
            region = view.word(region_start)
            regions.append(region)
        style = (sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE |
                 sublime.DRAW_SQUIGGLY_UNDERLINE)
        view.add_regions('python-lint-problem', regions, 'invalid',
                         'Packages/PythonChecker/images/marker.png', style)
