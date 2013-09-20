Python Checker
==============

A maintainable Python code checker for Sublime Text 3

![Screenshot](../screenshots/screenshot.png)

Once the plugin is installed, it will highlight common problems in your Python code.

Internally it relies on the wonderful `pyflakes` and `pep8` packages.

Installation
------------

Use [Package Control](https://sublime.wbond.net/).

Python version
--------------

By default Python Checker will use the version of Python that came with Sublime Text 3. This currently means Python 3 and can result in problems like `undefined name 'unicode'` being reported. If you want to use a different version, set the `python_interpreter_path` option in your project settings:

```json
# <project name>.sublime-project
{
    "settings": {
        "python_interpreter_path": "/usr/bin/python"
    }
}
```

This is compatible with other plugins including [SublimeJEDI](https://github.com/srusskih/SublimeJEDI).

PEP8 checks
-----------

Use the standard `pep8` [configuration files](http://pep8.readthedocs.org/en/latest/intro.html#configuration) to control the behaviour including skipping some checks. An example project configration might look like this:

```ini
# setup.cfg or tox.ini
[pep8]
ignore = E501,W191
max-line-length = 120
```
