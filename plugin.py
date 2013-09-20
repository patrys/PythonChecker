import os.path

import sublime
import sublime_plugin

from . import checker

PACKAGE_NAME = os.path.splitext(os.path.basename(os.path.dirname(__file__)))[0]


class Validator(sublime_plugin.EventListener):

    KNOWN_SYNTAXES = {'Packages/Python/Python.tmLanguage'}

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
                view.set_status('python-checker-problem', error)
            else:
                view.erase_status('python-checker-problem')

    def get_selected_line(self, view):
        selection = view.sel()
        try:
            return view.rowcol(selection[0].end())[0]
        except Exception:
            return None

    def revalidate(self, view):
        if view.settings().get("syntax") not in self.KNOWN_SYNTAXES:
            return
        problems = self.get_problems(view)
        self.highlight_problems(view, problems)
        self.update_statusbar(view, force=True)

    def get_problems(self, view):
        filename = view.file_name()
        if not filename:
            filename = '<unsaved>'
        source = view.substr(sublime.Region(0, view.size()))
        settings = view.settings()
        python_executable = settings.get('python_interpreter_path', None)
        if python_executable:
            return checker.get_external(source, filename,
                                        executable=python_executable)
        return checker.get_problems(source, filename)

    def highlight_problems(self, view, problems):
        view.erase_regions('python-checker-problem')
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
        view.add_regions('python-checker-problem', regions, 'invalid',
                         'Packages/%s/images/marker.png' % (PACKAGE_NAME,),
                         style)
