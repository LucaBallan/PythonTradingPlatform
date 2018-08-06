import sys
import platform
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from typing import Optional
from functools import partial


#
#
#
class Console:
    # bool
    standard_console = None
    use_input = None
    # main objects
    completer = None
    history = None
    auto_suggest = None
    ctrl_c_command = None

    def __init__(self, words_list: list, history_filename: Optional[str], ctrl_c_command: str, auto_suggest: bool):
        self.ctrl_c_command = ctrl_c_command
        if hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
            self.standard_console = True
            self.completer = WordCompleter(words_list, ignore_case=False)
            self.history = FileHistory(history_filename) if history_filename is not None else InMemoryHistory()
            self.auto_suggest = AutoSuggestFromHistory() if auto_suggest else None

        else:
            self.standard_console = False  # inside IDE
            if platform.system() == 'Windows':
                self.use_input_mod = True
            else:
                self.use_input_mod = True

    #
    #
    #
    def prompt(self, prompt_text) -> str:
        try:
            if self.standard_console:
                user_input = prompt(prompt_text, history=self.history, auto_suggest=self.auto_suggest, completer=self.completer)
            else:
                if self.use_input_mod:
                    user_input = input_mod(prompt_text)
                else:
                    user_input = input(prompt_text)
        except KeyboardInterrupt:
            return self.ctrl_c_command
        return user_input

    #
    #
    #
    def prompt_selection(self, prompt_text, validate, default):
        while True:
            try:
                if self.standard_console:
                    user_input = prompt(prompt_text)
                else:
                    if self.use_input_mod:
                        user_input = input_mod(prompt_text)
                    else:
                        user_input = input(prompt_text)
            except KeyboardInterrupt:
                return default
            if user_input == '':
                return default
            user_input = validate(user_input)
            if user_input is not None:
                break
        return user_input

    #
    #
    #
    @staticmethod
    def str_from(str_list: list):
        def internal_str_from(txt: str, internal_str_list: list):
            txt = txt.strip()
            if txt in internal_str_list:
                return txt
            return None

        return partial(internal_str_from, internal_str_list=str_list)

    #
    #
    #
    @staticmethod
    def int_from(int_list: list):
        def internal_int_from(txt: str, internal_int_list: list):
            try:
                txt = int(float(txt))
            except ValueError:
                return None
            if txt in internal_int_list:
                return txt
            return None

        return partial(internal_int_from, internal_int_list=int_list)


#
#
#
def input_mod(txt):
    sys.stdout.write(txt)
    sys.stdout.flush()
    i = sys.stdin.readline()
    return i.strip()
