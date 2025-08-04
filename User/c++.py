import sublime
import sublime_plugin

class SetDefaultSyntaxCommand(sublime_plugin.EventListener):
    def on_new(self, view):
        view.set_syntax_file('Packages/C++/C++.sublime-syntax')