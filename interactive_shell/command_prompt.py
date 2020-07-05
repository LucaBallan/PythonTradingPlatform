from typing import Sequence, Dict

from interactive_shell.console import Console


#
#
#
def command_prompt(console: Console,
                   action_table_: Sequence[list],
                   list_aliases: Dict[str, str] = None,
                   aux_data: dict = None) -> None:
    """
    action_table_ = [ ['action_name', [min_num_parameters, fnc, param_desc, line_desc, [help_fnc]], ....

                    NB: 1) []        -> create empty space in the help
                        2) ''        -> default action, must be in the table
                        3) 'action'  -> must be lower case

    list_aliases = { 'alias': 'action_name', ....
    """
    #
    # define structure
    #
    action_table = dict()
    for element in action_table_:
        if len(element) != 0:
            action_table[element[0]] = element[1]
    if '' not in action_table:
        raise ValueError('default action must be in action_table')
    default_action = action_table[''][1]

    #
    # define format
    #
    format_cmd = max([len(a_key) for a_key in action_table]) + 2
    format_arg = max([len(action_table[a_key][2]) for a_key in action_table if len(action_table[a_key]) > 2]) + 2

    #
    # loop
    #
    while True:
        argv = console.prompt('> ')
        argv = argv.split()
        if len(argv) == 0:
            default_action([], aux_data)
            continue

        action = get_action(argv[0], list_aliases)
        params = argv[1:]

        #
        # help
        #
        if action == '?' or action == 'help':
            if len(params) > 0:
                # display action help
                action = get_action(params[0], list_aliases)
                if action in action_table:
                    action_desc = action_table[action]
                    print(action + ' ' + action_desc[2])
                    if len(action_desc) > 4:
                        action_desc[4]()
                else:
                    print('command not found ' + action)
            else:
                # display full help
                print('help'.ljust(format_cmd) + ' '.ljust(format_arg) + 'display this help')
                for element in action_table_:
                    if len(element) == 0:
                        print('')
                        continue
                    if len(element[1]) < 4:
                        continue
                    print(element[0].ljust(format_cmd) + element[1][2].ljust(format_arg) + element[1][3])
            default_action([], aux_data)
            continue

        #
        # wrong action
        #
        if action not in action_table:
            print('command not found ' + ' '.join(argv))
            default_action([], aux_data)
            continue
        action_desc = action_table[action]

        # required parameters
        if len(params) < action_desc[0]:
            print(action + ' ' + action_desc[2])
            default_action([], aux_data)
            continue

        # action
        ret = action_desc[1](params, aux_data)

        # parse return
        if isinstance(ret, str):
            print(action + ' ' + action_desc[2])
            print(ret)
            continue

        if ret:
            break


#
#
#
def get_action(action: str, list_aliases: dict):
    action = action.lower()
    #
    # alias
    #
    if list_aliases is not None:
        if action in list_aliases:
            action = list_aliases[action]
    return action
