import platform
import sys
from functools import partial
from typing import Optional, Callable, Sequence, List, Union, Any

from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory, InMemoryHistory


#
#
#
class Console:
    #
    #
    #
    def __init__(self, words_list: List[str], history_filename: Optional[str], ctrl_c_command: str, auto_suggest: bool):

        self.__completer = None
        self.__history = None
        self.__auto_suggest = None
        self.__use_windows_prompt = None

        self.__ctrl_c_command = ctrl_c_command
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            self.__use_standard_console = True
            self.__completer = WordCompleter(words_list, ignore_case=False)
            self.__history = FileHistory(history_filename) if history_filename is not None else InMemoryHistory()
            self.__auto_suggest = AutoSuggestFromHistory() if auto_suggest else None
        else:
            # Console inside an IDE.
            self.__use_standard_console = False
            self.__use_windows_prompt = True if platform.system() == 'Windows' else True  # TODO Always True

    #
    #
    #
    def prompt(self, prompt_text: str) -> str:
        """Request for user input.

        Args:
            prompt_text: Prompt text.

        Returns:
            User input.
        """
        try:
            if self.__use_standard_console:
                user_input = prompt(prompt_text,
                                    history=self.__history,
                                    auto_suggest=self.__auto_suggest,
                                    completer=self.__completer)
            else:
                user_input = self.__alt_prompt(prompt_text)
        except KeyboardInterrupt:
            return self.__ctrl_c_command
        return user_input

    #
    #
    #
    def prompt_selection(self,
                         prompt_text: str,
                         validate: Union[Callable[[str], Optional[Any]], partial],
                         default: Any) -> Any:
        """Request for user selection.

        Args:
            prompt_text: Prompt text.
            validate: Function that validate the user input.
            default: Default user choice in case of CTRL-C or null input.

        Returns:
            User choice.
        """
        while True:
            try:
                if self.__use_standard_console:
                    user_input = prompt(prompt_text)
                else:
                    user_input = self.__alt_prompt(prompt_text)
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
    def str_from(str_list: Sequence[str]) -> Union[Callable[[str], Optional[str]], partial]:
        """Select a string from a list."""
        def internal_str_from(txt: str, internal_str_list: Sequence[str]) -> Optional[str]:
            txt = txt.strip()
            if txt in internal_str_list:
                return txt
            return None

        return partial(internal_str_from, internal_str_list=str_list)

    #
    #
    #
    @staticmethod
    def int_from(int_list: Sequence[int]) -> Union[Callable[[str], Optional[int]], partial]:
        """Select an integer from a list."""
        def internal_int_from(txt: str, internal_int_list: Sequence[int]) -> Optional[int]:
            try:
                selected_integer = int(float(txt))
            except ValueError:
                return None
            if selected_integer in internal_int_list:
                return selected_integer
            return None

        return partial(internal_int_from, internal_int_list=int_list)

    #
    #
    #
    def __alt_prompt(self, prompt_text: str):
        """Alternate to console prompt."""
        if self.__use_windows_prompt:
            sys.stdout.write(prompt_text)
            sys.stdout.flush()
            i = sys.stdin.readline()
            return i.strip()
        return input(prompt_text)
