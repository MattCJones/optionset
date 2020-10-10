#!/usr/bin/env python3
"""
Optionset
~~~~~~~~

Enable/disable user-predefined options in text-based dictionaries.
Use -h to view help.

Author: Matthew C. Jones
Email: matt.c.jones.aoe@gmail.com

:copyright: 2020 by Optionset authors, see AUTHORS for more details.
:license: GPLv3, see LICENSE for more details.
"""

# Import files
import argparse
import logging
import os
import re

from collections import defaultdict, namedtuple, OrderedDict
from configparser import ConfigParser
from contextlib import contextmanager
from fnmatch import fnmatch
from functools import wraps
from pathlib import Path
from pprint import pformat
from sys import argv, exit
from time import time

__author__ = "Matthew C. Jones"
__version__ = "20.10.09"

__all__ = (
        "optionset",
        "__author__",
        "__version__",
        )

# ############################################################ #
# Set up global constants, variables, and parser
# ############################################################ #
# Set up global constants
BASENAME = Path(__file__).name
BASHCOMP_CMD = 'os'  # bash-completion run command
BASENAME_NO_EXT = Path(__file__).stem
RUNCMD = BASHCOMP_CMD if '--bash-completion' in argv else BASENAME
AUX_DIR = Path("~/.optionset").expanduser()
LOG_NAME = f"log.{BASENAME}"
BASHCOMP_NAME = "bash_completion"
CONFIG_NAME = f"{BASENAME_NO_EXT}.cfg"
SHORT_DESCRIPTION = f"""
Optionset allows users to succinctly set up and conduct parameter studies for
applications that reference text-based dictionary files. The program enables
and disables user-predefined options in text-based dictionary files in the base
directory and below.  The user specifies the lines in the files that will
either be enabled or disabled by adding macro commands as commented text.
"""
SHORT_HELP_DESCRIPTION = f"""{SHORT_DESCRIPTION}
Run '{RUNCMD} --help-full' to view more-detailed help"""
FULL_HELP_DESCRIPTION = f"""{SHORT_DESCRIPTION}
For example, suppose a parameter study involved varying fluid properties and
the kinematic viscosity was listed in a dictionary file as,

    nu = 1.5e-5; // air [m^2/s]
    //nu = 1e-6; // water [m^2/s]

In the above text, the property of water will be ignored, since the second line
is commented out.  To enable water instead of air, the user could simply switch
which line is commented.  However, this task is often inconvenient, especially
with numerous variable properties listed across multiple files.  Alternatively,
the following macro instructions can be added to the commented part of the text
to mark them as a parameters to be varied.

    nu = 1.5e-5; // air [m^2/s] ~nu air
    //nu = 1e-6; // water [m^2/s] ~nu water

This setup allows the user to easily switch between air and water simulations
without manually editing the dictionary file.  On the command line, simply run,

    $ {RUNCMD} ~nu water

and the dictionary file will be modified and re-written as,

    //nu = 1.5e-5; // air [m^2/s] ~nu air
    nu = 1e-6; // water [m^2/s] ~nu water

so that water is now the active property. Within the prescribed macros, `~nu`
is the 'option' while `air` and `water` are the 'settings'.  An unlimited
number of arbitrary options and settings are allowed.  Each must be composed of
alphanumerical words with dots, pluses, minuses, and underscores, and the first
1+ characters in the option must be a symbol such as `~@$^&=|?`. Recognizable
comments are denoted by `//` `#` `%` `!` or `--`.

To avoid comment clutter, multi-line options are encouraged by annotating `*`
in front of the first and last options in a series (see text on left),

    functions        // *~forces on | <---  | functions        // ~forces on
    {{                               |INSTEAD| {{                // ~forces on
    #include "forces"               |  OF   | #include "forces"// ~forces on
    }}                // *~forces on | --->  | }}                // ~forces on
    //               // ~forces off |       | //               // ~forces off

An additional feature is the variable option.  For variable options the macro
command must be formatted with a Perl-styled regular expression `='<regex>'`
that matches the desired text to be changed with parentheses `()`, for example,

    rho = 1.225; // ~density ='rho = (.*);'

Here, `(.*)` matches `1.225` in `rho = 1.225;`.  To change this to `1025`, run
`{RUNCMD} ~density 1025`, and the line within the file now becomes,

    rho = 1025; // ~density ='rho = (.*);'

To view all of the available options and settings that have been prescribed,
run `{RUNCMD} -a`.  To narrow the search to options that start with `~nu`,
run `{RUNCMD} -a ~nu`. Additionally, `{RUNCMD} -a -f` will list all
associated file locations.

To enable Bash shell tab completion, add the following to your `~/.bashrc`,

    function {BASHCOMP_CMD} {{
        {BASENAME} "$@" --bash-completion;
        source {AUX_DIR/BASHCOMP_NAME};
    }}

and run the program using `{BASHCOMP_CMD}` instead of `{BASENAME}`.

Using your favorite scripting language, it is convenient to glue this program
into more advanced option variation routines to create parameter sweeps and
case studies.  While this program is generally called from the command line, it
is also possible to directly import this functionality into a Python script.

    from optionset import optionset
    optionset(['~nu', 'water'])  # set kinematic viscosity to that of water

For command line usage, the following arguments are permitted.
"""

# Default configuration
IGNORE_DIRS = ['.[a-zA-Z0-9]*', '__pycache__', '[0-9]', '[0-9][0-9]*',
               '[0-9].[0-9]*', 'log', 'logs', 'processor[0-9]*', 'archive',
               'trash',
               ]  # UNIX-based wild cards
IGNORE_FILES = [BASENAME, LOG_NAME, BASHCOMP_NAME, CONFIG_NAME, '.*', 'log.*',
                '*.log', '*.pyc', '*.gz', '*.png', '*.jpg', '*.obj', '*.stl',
                '*.stp', '*.step',
                ]  # UNIX-based wild cards
MAX_FLINES = 9999  # maximum lines per file
MAX_FSIZE_KB = 10  # maximum file size, kilobytes
DEFAULT_CONFIG = {'ignore_dirs': IGNORE_DIRS, 'ignore_files': IGNORE_FILES,
                  'max_flines': MAX_FLINES, 'max_fsize_kb': MAX_FSIZE_KB, }

# Regular expression frameworks
ANY_COMMENT_IND = r'(?://|[#%!]|--)'  # comment indicators: // # % ! --
MULTI_TAG = r'[*]'  # for multi-line commenting
ANY_WORD = r'[a-zA-Z0-9._\-\+]+'
ANY_RAW_OPTN = ANY_WORD
ANY_QUOTE = r'[\'"]'
ANY_VAR_SETTING = rf'\={ANY_QUOTE}.+{ANY_QUOTE}'
ANY_SETTING = rf'(?:{ANY_WORD}|{ANY_VAR_SETTING})'
VALID_INPUT_SETTING = rf'(?: |{ANY_WORD})+'  # words with spaces (using '')
BRACKETS = r'[()<>\[\]]'
# Implicitely match tag. Do not include any of these:
ANY_TAG = (rf'(?:(?!\s|{ANY_COMMENT_IND}|{MULTI_TAG}|{ANY_WORD}|{BRACKETS}'
           rf'|{ANY_QUOTE}).)')
# Explicitely specify tag with: ANY_TAG = r'[~@$^&\=\|\?]'
WHOLE_COMMENT = (r'(?P<com_ind>{com_ind})'
                 r'(?P<whole_com>.*\s+{mtag}*{tag}+{raw_opt}'
                 r'\s+{setting}\s.*\n?)')
UNCOMMD_LINE = (r'^(?P<nested_com_inds>{nested_com_inds})'
                r'(?P<non_com>\s*(?:(?!{com_ind}).)+)' + WHOLE_COMMENT)
COMMD_LINE = (r'^(?P<nested_com_inds>{nested_com_inds})'
              r'(?P<non_com>\s*{com_ind}(?:(?!{com_ind}).)+)' + WHOLE_COMMENT)
ONLY_OPTN_SETTING = r'({mtag}*)({tag}+)({raw_opt})\s+({setting})\s?'
GENERIC_RE_VARS = {'com_ind': ANY_COMMENT_IND, 'mtag': MULTI_TAG,
                   'tag': ANY_TAG, 'raw_opt': ANY_RAW_OPTN,
                   'setting': ANY_SETTING, 'nested_com_inds': ''}

# Error messages
INCOMPLETE_INPUT_MSG = f'''InputError:
Incomplete input. Try:
    "{RUNCMD} -h"                    to view help
    "{RUNCMD} -a"                    to view available options
    "{RUNCMD} -a <unix expression>"  to search options using a unix expression
    "{RUNCMD} <option> <setting>"    to set the <setting> of <option>'''
INVALID_OPTN_MSG = f'''InputError:
Invalid option name. A preceding tag, such as '@' in '@option' is required, and
the rest of the option must adhere to the following regular expression:
{ANY_WORD}
To view help try:
    "{RUNCMD} -h"'''
INVALID_SETTING_MSG = f'''InputError:
Invalid setting name. The setting name must adhere to the following regular
expression: {ANY_WORD}
To view help try:
    "{RUNCMD} -h"'''
INVALID_VAR_REGEX_MSG = r'''FormatError:
Invalid 'variable setting' regular expression. The commented regular expression
must adhere to this form: %(anyVar)s
(e.i. an equals sign followed by a user specified regular expression in quotes)
Additionally, the corresponding code on the line of this 'variable setting'
must match the user specified regular expression in quotes. This regular
expression must have one and only one set of parentheses surrounding the
variable option to be matched such as '(.*)'.  Otherwise, To specify literal
parentheses in the regex, use '\('.
\r\nFile:{filename}
Line {line_num}:{line}
To view help try:
    "%(runCmd)s -h"''' % {'anyVar': ANY_VAR_SETTING, 'runCmd': RUNCMD}
INVALID_REGEX_GROUP_MSG = '''InvalidRegexGroupError: {specific_problem}
A regular expression 'group' is denoted by a surrounding pair of parentheses
'()' The commented variable setting should be the only group.' Use '()' to
surround only the variable setting group in the commented regular expression.
'''
INVALID_CONFIG_FILE_MSG = '''InvalidConfigFileError:
Problem reading {none_keys}
From {config_file}
Remove the file or correct the errors.
Exiting. '''

# Initialize global parser
parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, prog=RUNCMD,
        description=SHORT_HELP_DESCRIPTION)
parser.add_argument(
        'option', metavar='option', nargs='?', type=str, default="",
        help='\'option\' name')
parser.add_argument(
        'setting', metavar='setting', nargs='?', type=str, default="",
        help='\'setting\' for given \'option\'')
parser.add_argument(
        '-H', '--help-full', dest='help_full', default=False,
        action='store_true',
        help=f"show full help message and exit")
parser.add_argument(
        '-a', '--available', dest='available', default=False,
        action='store_true',
        help=("show available option-setting combinations; "
              "allows for unix-style glob-expression searching; "
              "'-a' is implicitely enabled when no 'setting' is input"))
parser.add_argument(
        '-f', '--show-files', dest='showfiles', default=False,
        action='store_true',
        help=f"show files associate with available options")
parser.add_argument(
        '-v', '--verbose', dest='verbose', default=False, action='store_true',
        help="turn on verbose output")
parser.add_argument(
        '-q', '--quiet', dest='quiet', default=False, action='store_true',
        help="turn off all standard output")
parser.add_argument(
        '-d', '--debug', dest='debug', default=False, action='store_true',
        help="turn on debug output in log file")
parser.add_argument(
        '-n', '--no-log', dest='no_log', default=False, action='store_true',
        help=f"do not write log file to '{AUX_DIR/LOG_NAME}'")
parser.add_argument(
        '--rename-option', dest='rename', metavar='', default='',
        help=("rename input option in all files"))
parser.add_argument(
        '--bash-completion', dest='bashcomp', default=False,
        action='store_true',
        help=("auto-generate bash tab-completion script "
              f"'{AUX_DIR/BASHCOMP_NAME}'"))
parser.add_argument(
        '--version', dest='version', default=False, action='store_true',
        help="show version and exit")
parser.add_argument(
        '--auxiliary-dir', dest='aux_dir', type=str,
        default=AUX_DIR, help=argparse.SUPPRESS)

# Initialize global variables
g_f_quiet = False
g_f_verbose = False

# ############################################################ #
# Define classes
# ############################################################ #


class FileVarsDatabase:
    """Data structure to hold variables used in file processing.
       Input file path, user input structure, and comment index.
    """
    def __init__(self, filepath, input_db):
        """Initialize variables. """
        self.filepath = filepath
        self.input_db = input_db

        self.f_filemodified = False  # True if file is modified
        self.f_multiline_active = False  # if active, toggle line
        self.f_multicommd = None  # True if multi-line option is commented
        self.nested_lvl = 0  # +1 level every commented multi-line option
        self.nested_increment = 0  # increments the nested level

        # Get string that signifies a commented line
        self.com_ind = _get_comment_indicator(filepath)

        # Prepare regular expressions
        self.re_vars = GENERIC_RE_VARS
        self.re_vars['com_ind'] = self.com_ind  # set file-specific indicator

        # Prepare nested option database
        self.nested_optn_db = OrderedDict()


# ############################################################ #
# Define utility functions
# ############################################################ #

def _print_and_log(print_str):
    """Print to standard out and INFO level in log. """
    logging.info(print_str)
    if not g_f_quiet:
        print(print_str)


def _log_before_after_commenting(func):
    """Wrapper to add file modifications to the log file. """
    @wraps(func)
    def log(*args_, **kwargs):
        line_, line_num_ = args_[0], args_[1]
        line_before_mod = '[{:>4} ]{}'.format(line_num_,
                                              line_.rstrip('\r\n'))
        return_str = func(*args_, **kwargs)
        line_after_mod = '[{:>4}\']{}'.format(line_num_,
                                              return_str.rstrip('\r\n'))
        if g_f_verbose:
            _print_and_log(line_before_mod)
            _print_and_log(line_after_mod)
        else:
            logging.info(line_before_mod)
            logging.info(line_after_mod)
        return return_str
    return log


@_log_before_after_commenting  # requires line, line_num as first args
def _uncomment(line, line_num, com_ind):
    """Uncomment a line. Input requires comment indicator string. """
    line = re.sub(rf'^(\s*)({com_ind})', r"\1", line)
    return line


@_log_before_after_commenting  # requires line, line_num as first args
def _comment(line, line_num, com_ind):
    """Comment a line. Input requires comment indicator string. """
    line = com_ind + line
    return line


@contextmanager
def _handle_errors(err_types, msg):
    """Use 'with:' to handle an error and print a message. """
    try:
        yield
    except err_types as err:
        _print_and_log(msg)
        logging.debug(err)
        exit()


def _write_bashcompletion_file(ops_db, var_ops_db,
                               bashcomp_path=AUX_DIR/BASHCOMP_NAME):
    """Write file that can be sourced to enable tab completion for this tool.
    """
    help_str = parser.format_help()
    re_short_usage = re.compile(r"\s(-\w+)")
    re_long_usage = re.compile(r"\s(--[a-zA-Z\-]+)")
    default_cmd_opts_short = [
        f"'{opt}'" for opt in sorted(re_short_usage.findall(help_str))]
    default_cmd_opts_long = [
        f"'{opt}'" for opt in sorted(re_long_usage.findall(help_str))]
    default_cmd_opts_short_str = ' '.join(default_cmd_opts_short)
    default_cmd_opts_long_str = ' '.join(default_cmd_opts_long)
    file_contents_template = r"""#!/bin/bash
# Auto-generated Bash completion settings for {base_run_cmd}
# Run 'source {bashcomp_path}' to enable
optRegex="\-[a-z], --[a-z]*"
_optionset()
{{
    local cur prev

    cur=${{COMP_WORDS[COMP_CWORD]}}
    prev=${{COMP_WORDS[COMP_CWORD-1]}}

    case ${{COMP_CWORD}} in
        1)
            COMPREPLY=($(compgen -W "
                {default_cmd_opts_short_str}
                {default_cmd_opts_long_str}{gathered_optns_str}
                " -- ${{cur}}))
            ;;
        2)
            case ${{prev}} in {optns_with_settings_str}
            esac
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
}}
complete -F _optionset {bashcomp_cmd}
complete -F _optionset {bashcomp_cmd_b}"""
    gathered_optns_str = ""
    optns_with_settings_template = """
                {optn_str})
                    COMPREPLY=($(compgen -W "{settings_str}" -- ${{cur}}))
                    ;;"""
    optns_with_settings_str = ""
    bashcomp_cmd = BASHCOMP_CMD
    bashcomp_cmd_b = BASENAME_NO_EXT
    base_run_cmd = BASENAME

    for db in (ops_db, var_ops_db):
        for item in sorted(db.items()):
            optn_str = item[0].replace(r'$', r'\$')
            gathered_optns_str += os.linesep
            gathered_optns_str += f"                '{optn_str}'"
            settings_str = ""
            for sub_item in sorted(item[1].items()):
                setting_str = sub_item[0]
                settings_str += " " + f"'{setting_str}'"
            optns_with_settings_str += \
                optns_with_settings_template.format(**locals())

    file_contents = file_contents_template.format(**locals())

    # Add convenient debug command that references in-development code
    if logging.getLevelName(logging.root.level) == "DEBUG":
        file_contents += "complete -F _optionset debug_os"

    with open(bashcomp_path, 'w', encoding='UTF-8') as file:
        logging.info(f"Writing Bash completion settings to {bashcomp_path}")
        file.writelines(file_contents)


def _print_available(ops_db, var_ops_db, show_files_db, glob_pat='*',
                     f_available=True):
    """Print available options and options for use; optionally sort with unix
    expression. """
    common_files = []
    body_msg = ""
    for db in (ops_db, var_ops_db):
        logging.info(pformat(db, indent=1))
        for item in sorted(db.items()):
            optn_str = item[0]
            if not fnmatch(optn_str, glob_pat):
                continue
            body_msg += os.linesep + f"  {optn_str}"
            if f_available:
                for sub_item in sorted(item[1].items()):
                    setting_str = sub_item[0]
                    if sub_item[1] is True:
                        left_str, right_str = '>', '<'
                    elif sub_item[1] is False:
                        left_str, right_str = ' ', ' '
                    elif sub_item[1] is None:
                        left_str, right_str = ' ', ' '
                    elif sub_item[1] is not None:
                        left_str, right_str = sub_item[1], sub_item[1]
                    else:
                        left_str, right_str = '?', '?'
                    body_msg += os.linesep
                    body_msg += f"\t{left_str} {setting_str} {right_str}"
            if show_files_db is not None:
                if show_files_db[optn_str]:
                    files_str = ' '.join(show_files_db[optn_str].keys())
                    body_msg += os.linesep + "  " + files_str + os.linesep
                    body_msg += "-"*60
                    for file_ in show_files_db[optn_str].keys():
                        common_files.append(file_)

    sub_hdr_msg = r"('  inactive  ', '> active <', '? both ?', '= variable =')"
    if body_msg == "":
        hdr_msg = f"No available options and settings matching '{glob_pat}'"
    else:
        hdr_msg = ("Showing available options and settings matching "
                   f"'{glob_pat}'")
        hdr_msg += os.linesep + sub_hdr_msg

    # Find files common to all options
    num_optns = len(common_files)
    if show_files_db is not None and num_optns > 1:
        common_files_str = "  Common files:" + os.linesep + "  "
        for common_file in sorted(set(common_files)):
            common_files_str += str(common_file).lstrip("'").rstrip("'") + " "
        body_msg += os.linesep + common_files_str

    full_msg = hdr_msg + body_msg
    _print_and_log(full_msg)


def _add_left_right_groups(inline_re):
    r"""Add left and right groups to regex.
    For example: \( (.*) 0 0 \) becomes (\( )(.*)( 0 0 \)) """
    # Must add one to get rid of preceding character match
    left_paren_ind = re.search(r'[^\\]([\(])', inline_re).start() + 1
    right_paren_ind = re.search(r'[^\\]([\)])', inline_re).start() + 1
    left = inline_re[:left_paren_ind]
    mid = inline_re[left_paren_ind:right_paren_ind + 1]
    right = inline_re[right_paren_ind + 1:]
    new_inline_re = f"({left}){mid}({right})"
    return new_inline_re


@_log_before_after_commenting  # requires line, line_num as first args
def _set_var_optn(line, line_num, com_ind, str_to_replace, setting,
                  nested_com_inds, non_com, whole_com):
    """Return line with new variable option set. """
    # Add 2 new groups, one for the left side and the other for the right
    inline_re = _strip_setting_regex(setting)
    logging.info(f"Setting variable option:{inline_re}:{str_to_replace}")
    new_inline_re = _add_left_right_groups(inline_re)

    def surround_var_str(re_match):
        """Surround variable option string with proper text. """
        return re_match.group(1) + str_to_replace + re_match.group(3)
    new_non_com = re.sub(new_inline_re, surround_var_str, non_com)
    newline = nested_com_inds + new_non_com + com_ind + whole_com
    return newline


def _skip_file_warning(filename, reason):
    """Log a warning that the current file is being skipped. """
    logging.warning(f"Skipping: {filename}")
    logging.warning(f"Reason: {reason}")


def _yield_utf8(file_):
    """Yield file lines only if they are UTF-8 encoded (non-binary). """
    try:
        for line in file_:
            yield line
    except UnicodeDecodeError as err:
        _skip_file_warning(file_.name, err)


def _line_count(filename, line_limit):
    """Return number of lines in a file unless file exceeds line limit. """
    linecount = 0
    with open(filename, 'r', encoding='UTF-8') as file:
        for _ in _yield_utf8(file):
            linecount += 1
            if linecount > line_limit:
                return linecount + 1  # return line limit +1
    return linecount


def _get_comment_indicator(filename):
    """Get comment indicator from filename ('#', '%', '!', '//', or '--'). """
    with open(filename, 'r', encoding='UTF-8') as file:
        commd_line_re = re.compile(rf'^\s*({ANY_COMMENT_IND}).*')
        for line in _yield_utf8(file):
            search_commd_line = commd_line_re.search(line)
            if search_commd_line:
                return search_commd_line.group(1)

        logging.debug('Comment not found at start of line. Searching in-line.')
        uncommd_line_re = re.compile(UNCOMMD_LINE.format(**GENERIC_RE_VARS))
        file.seek(0)  # restart file
        for line in _yield_utf8(file):
            search_uncommd_line = uncommd_line_re.search(line)
            if search_uncommd_line:
                return search_uncommd_line.group('com_ind')

    return None


def _check_varop_groups(re_str):
    """Calculate the number of regex groups designated by (). """
    all_groups = re.findall(r'([^\\]\(.*?[^\\]\))', re_str)
    if all_groups:
        if len(all_groups) > 1:
            _print_and_log(INVALID_REGEX_GROUP_MSG.format(
                specific_problem='More than one regex group \'()\' found'))
            raise AttributeError
    else:
        _print_and_log(INVALID_REGEX_GROUP_MSG.format(
            specific_problem='No regex groups found.\r\n'))
        raise AttributeError


def _strip_setting_regex(setting_str):
    """Return in-line regular expression using setting."""
    return setting_str[2:-1]  # remove surrounding =''


def _parse_inline_regex(non_commented_text, setting, var_err_msg=""):
    """Parse variable option value using user-defined regular expression
    stored in 'setting'.
    """
    # Attribute handles regex fail. Index handles .group() fail
    with _handle_errors(err_types=(AttributeError, IndexError, re.error),
                        msg=var_err_msg):
        inline_re = _strip_setting_regex(setting)
        _check_varop_groups(inline_re)
        str_to_replace = re.search(inline_re, non_commented_text).group(1)
    return str_to_replace


def _process_line(line, line_num, fdb, optns_settings_db,
                  var_optns_values_db, show_files_db):
    """Apply logic and process options/settings in a single line of the current
    file.  This is the heart of the code.

    Terminology is explained by referring to the following example lines,

    // somefile.txt start of file
    Some code here. // some comment here @option_a setting_a
    //Some            // nested_lvl is 0 here *@option_a setting_b
    //other           // nested_lvl is 1 here
    //code            // nested_lvl is 1 here @option_b setting_a
    //here.           // nested_lvl is 0 here *@option_a setting_b
    Final code.     // nested_lvl is 0 here @option_b setting_b
    End of file.

    com_ind:     '//' is extracted comment indicator; this denotes a comment
    option:     '@option_a' and '@option_b' are extracted options
    tag:        '@' is the extracted tag for '@option_a' and '@option_b'
    raw_opt:     'option_a' and 'option_b' are the extracted raw options
    setting:    'setting_a' and 'setting_b' are extracted settings
    mtag:       '*' is the multi-tag, which indicates a multi-line option, in
                this case for '@option_a setting_b'
    nested_lvl:  '0' is starting level; when a multi-line option is found, the
                nested_lvl is increased by 1. '@option_b' is a nested option
                because it lies within the multi-line '@option_a setting_b'
    (in)active: An option-setting combination on an uncommented line is active.
                Nested options also account for the nested level. In the above
                example, '@option_a setting_a' and '@option_b setting_b' are
                active, while '@option_a setting_b' and '@option_b setting_b'
                are inactive.
    """
    newline = line
    inp = fdb.input_db
    var_err_msg = INVALID_VAR_REGEX_MSG.format(filename=fdb.filepath,
                                               line_num=line_num, line=line)

    # Adjust nested level
    fdb.nested_lvl += fdb.nested_increment
    fdb.nested_increment = 0  # reset
    fdb.re_vars['nested_com_inds'] = rf"\s*{fdb.com_ind}" * fdb.nested_lvl

    # Identify components of line based on regular expressions
    commd_line_re = re.compile(COMMD_LINE.format(**fdb.re_vars))
    uncommd_line_re = re.compile(UNCOMMD_LINE.format(**fdb.re_vars))
    tag_optn_setting_re = re.compile(ONLY_OPTN_SETTING.format(**fdb.re_vars))
    commd_line_match = commd_line_re.search(line)
    uncommd_line_match = uncommd_line_re.search(line)
    if commd_line_match:  # must search for commented before uncommented
        nested_com_inds, non_com, whole_com =\
                commd_line_match.group('nested_com_inds', 'non_com',
                                       'whole_com')
    elif uncommd_line_match:
        nested_com_inds, non_com, whole_com =\
                uncommd_line_match.group('nested_com_inds', 'non_com',
                                         'whole_com')
    else:
        nested_com_inds, non_com, whole_com = "", "", ""
    f_comment = bool(commd_line_match)
    tag_optn_setting_matches = tag_optn_setting_re.findall(whole_com)

    logging.debug(f"LINE[{line_num}](L{fdb.nested_lvl:1},"
                  f"{str(fdb.f_multiline_active)[0]})"
                  f"({fdb.com_ind},{str(f_comment)[0]}):{line[:-1]}")

    # Parse commented part of line; determine inline matches
    inline_optn_count = defaultdict(lambda: 0)
    inline_optn_match = defaultdict(lambda: False)
    inline_setting_match = defaultdict(lambda: False)
    f_inline_optn_match = False
    for mtag, tag, raw_opt, setting in tag_optn_setting_matches:
        # Build database of related file locations
        if inp.f_showfiles:
            show_files_db[tag+raw_opt][str(fdb.filepath)] = True
        # Count occurances of option
        inline_optn_count[tag+raw_opt] += 1
        if (inp.tag+inp.raw_opt).replace('\\', '') == tag+raw_opt:
            inline_optn_match[tag+raw_opt] = True
            f_inline_optn_match = True
            if inp.setting.replace('\\', '') == setting:
                inline_setting_match[tag+raw_opt] = True

    # If renaming an option; if option match, rename; finally return
    if not inp.rename_str == '':
        if f_inline_optn_match:
            re_rename_str = rf'({inp.tag+inp.raw_opt})(\s+{ANY_SETTING}\s?)'
            new_whole_com = re.sub(re_rename_str, rf"{inp.rename_str}\2",
                                   whole_com)
            newline = nested_com_inds + non_com + fdb.com_ind + new_whole_com
            fdb.f_filemodified = True
        return newline

    # Multi-line option logic:
    # Toggle (comment or uncomment) line if multi-line option is active
    if fdb.f_multiline_active and not f_inline_optn_match:
        if fdb.f_multicommd:
            newline = _uncomment(line, line_num, fdb.com_ind)
        else:
            newline = _comment(line, line_num, fdb.com_ind)
        f_freeze_changes = True
    else:
        f_freeze_changes = False

    # All other required logic based on matches in line
    for mtag, tag, raw_opt, setting in tag_optn_setting_matches:
        logging.debug(f"\tMATCH(freeze={str(f_freeze_changes)[0]}):"
                      f"{mtag}{tag}{raw_opt} {setting}")
        # Skip rest of logic if change-freeze is set
        if f_freeze_changes:
            continue

        # Logic for determining levels for nested options
        if mtag:  # multitag present in line
            if f_comment:
                fdb.nested_optn_db[fdb.nested_lvl] = tag+raw_opt
                fdb.nested_increment = 1
            else:  # uncommented
                if len(fdb.nested_optn_db) < 1:
                    pass
                elif fdb.nested_optn_db[fdb.nested_lvl-1] == tag+raw_opt:
                    fdb.nested_optn_db.pop(fdb.nested_lvl-1)
                    fdb.nested_increment = -1
                    f_comment = True
                    fdb.f_multiline_active = False
                    f_freeze_changes = True
                    if inline_setting_match[tag+raw_opt]:
                        # Uncomment if match input setting
                        newline = _uncomment(line, line_num, fdb.com_ind)
                    continue
        else:  # no multitag present
            pass

        # Build database of available options and settings
        if inp.f_available or inp.f_showfiles or inp.f_bashcomp:
            # Determine active, inactive, and simultaneous options
            if re.search(ANY_VAR_SETTING, setting) and not f_comment:
                str_to_replace = _parse_inline_regex(non_com, setting,
                                                     var_err_msg)
                var_optns_values_db[tag+raw_opt][str_to_replace] = '='
            elif optns_settings_db[tag+raw_opt][setting] is None:
                if inline_optn_count[tag+raw_opt] > 1:
                    optns_settings_db[tag+raw_opt][setting] = None
                else:
                    optns_settings_db[tag+raw_opt][setting] = (not f_comment)
            elif optns_settings_db[tag+raw_opt][setting] != (not f_comment):
                optns_settings_db[tag+raw_opt][setting] = '?'  # ambiguous
            else:
                pass

        # Modify line based on user input and regular expression matches
        if not (inp.f_available or inp.f_showfiles):
            # Match input option (tag+raw_opt)
            if (inp.tag+inp.raw_opt).replace('\\', '') == tag+raw_opt:
                if f_comment:  # commented line
                    if inp.setting == setting:  # match input setting
                        # Uncomment lines with input tag+raw_opt and setting
                        newline = _uncomment(line, line_num, fdb.com_ind)
                        if mtag and not fdb.f_multiline_active:
                            fdb.f_multiline_active = True
                            fdb.f_multicommd = f_comment
                        elif mtag and fdb.f_multiline_active:
                            fdb.f_multiline_active = False
                            fdb.f_multicommd = None
                    else:  # setting does not match
                        pass
                else:  # uncommented line
                    # If variable option, use input regex to modify line
                    if re.search(ANY_VAR_SETTING, setting):
                        str_to_replace = _parse_inline_regex(non_com, setting,
                                                             var_err_msg)
                        replace_str = inp.setting
                        if replace_str == str_to_replace:
                            logging.info(f"Option already set: {replace_str}")
                        else:
                            with _handle_errors(err_types=AttributeError,
                                                msg=var_err_msg):
                                newline = _set_var_optn(
                                    line, line_num, fdb.com_ind, replace_str,
                                    setting, nested_com_inds, non_com,
                                    whole_com)
                                f_freeze_changes = True
                    # Not 1 match in line
                    elif (inline_optn_match[tag+raw_opt]) and\
                            (not inline_setting_match[tag+raw_opt]):
                        newline = _comment(line, line_num, fdb.com_ind)
                        if mtag and not fdb.f_multiline_active:
                            fdb.f_multiline_active = True
                            fdb.f_multicommd = f_comment
                            f_freeze_changes = True
                        elif mtag and fdb.f_multiline_active:
                            fdb.f_multiline_active = False
                            fdb.f_multicommd = None
                            f_freeze_changes = True
                        else:
                            pass
                    else:
                        pass
            else:
                pass
        else:
            pass

    if not newline == line:  # if 1 line in file is changed, file is modified
        fdb.f_filemodified = True

    return newline


def _process_file(filepath, input_db, optns_settings_db,
                  var_optns_values_db, show_files_db):
    """Process individual file.
    Update optns_settings_db and var_optns_values_db
    Return if changes have been made or not

    General algorithm is to scroll through file line by line, applying
    consistent logic to make build database of available options or to make the
    desired changes.
    """
    logging.debug(f"FILE CANDIDATE: {filepath}")

    # Check file size and line count of file
    linecount = _line_count(filepath, line_limit=input_db.max_flines)
    fsize_kb = filepath.stat().st_size/1000
    if fsize_kb > input_db.max_fsize_kb:
        reason_str = f"File exceeds kB size limit of {input_db.max_fsize_kb}"
        _skip_file_warning(filepath, reason=reason_str)
        return False

    if linecount > input_db.max_flines:
        reason_str = f"File exceeds line limit of {input_db.max_flines}"
        _skip_file_warning(filepath,
                           reason=reason_str)
        return False

    # Instantiate and initialize file variables
    fdb = FileVarsDatabase(filepath, input_db)

    # Only continue if a comment index is found in the file
    if not fdb.com_ind:
        return False
    logging.debug(f"FILE MATCHED [{fdb.com_ind}]: {filepath}")

    # Read file and parse options in comments
    with open(filepath, 'r', encoding='UTF-8') as file:
        newlines = ['']*linecount
        for idx, line in enumerate(_yield_utf8(file)):
            line_num = idx + 1
            newlines[idx] = _process_line(line, line_num, fdb,
                                          optns_settings_db,
                                          var_optns_values_db, show_files_db)

    # Write file
    if fdb.f_filemodified:
        with open(filepath, 'w', encoding='UTF-8') as file:
            file.writelines(newlines)
        _print_and_log(f"File modified: {file.name}")
        return True

    return False


def _scroll_through_files(valid_files, input_db):
    """Scroll through files, line by line. This function:
    * This is heart of the code. """
    inp = input_db
    optns_settings_db = defaultdict(lambda: defaultdict(lambda: None))
    var_optns_values_db = defaultdict(lambda: defaultdict(lambda: None))
    if inp.f_showfiles:
        show_files_db = defaultdict(lambda: defaultdict(lambda: None))
    else:
        show_files_db = None
    f_changes_made = False

    if inp.f_available or inp.f_showfiles:
        logging.info(("Scrolling through files to gather available options and"
                      " settings data"))
    else:
        logging.info(("Scrolling through files to set: {inp.tag}{inp.raw_opt} "
                      "{inp.setting}").format(inp=input_db))

    for filepath in valid_files:
        f_file_changed = _process_file(filepath, input_db, optns_settings_db,
                                       var_optns_values_db, show_files_db)
        if f_file_changed:
            f_changes_made = True

    # Cut out options with a singular setting. Could try filter() here
    optns_settings_db = {
        tg: n for tg, n in optns_settings_db.items() if len(n) > 1}

    return (optns_settings_db, var_optns_values_db, show_files_db,
            f_changes_made)


def _fn_compare(glob_set, compare_array):
    """Compare set with unix * expressions with array of files or directories.
    """
    for glob_ in glob_set:
        for cmpr in compare_array:
            if fnmatch(cmpr, glob_):
                return True
    return False


def _gen_valid_files(ignore_files, ignore_dirs):
    """Generator to get non-ignored files in non-ignored directories. """
    for dirpath, _, files in os.walk('.', followlinks=True):
        if not _fn_compare(ignore_dirs, dirpath.split(os.sep)):
            for file_ in files:
                baseFileName = Path(file_).name
                if not _fn_compare(ignore_files, (baseFileName,)):
                    yield Path(f"{dirpath}/{file_}")


def _str_dict(dict_):
    """Return dictionary with string representation of arrays (no brackets).
    """
    return {k: str(v).lstrip('[').rstrip(']') for k, v in dict_.items()}


def _array_from_str(array_str):
    """Return an array from a string of an array. """
    if isinstance(array_str, str):
        arr = [a.replace("'", '').replace('"', '').strip()
               for a in array_str.split(',')]
    else:
        arr = None
    return arr


def _load_program_settings(args):
    """Load program settings if file provided by user, else use default. """
    config_file = Path(args.aux_dir) / f"{BASENAME_NO_EXT}.cfg"
    config = DEFAULT_CONFIG.copy()
    cfg = ConfigParser()
    cfg.optionxform = str  # maintain case even on Windows
    secn = 'Files'

    if Path.exists(config_file):
        logging.info(f"Reading program settings from {config_file}:")
        cfg.read(config_file)
        config['max_flines'] = int(cfg[secn].get('max_flines'))
        config['max_fsize_kb'] = int(cfg[secn].get('max_fsize_kb'))
        config['ignore_dirs'] = _array_from_str(cfg[secn].get('ignore_dirs'))
        config['ignore_files'] = _array_from_str(cfg[secn].get('ignore_files'))
        none_keys = []
        for key, val in config.items():
            if val is None:
                none_keys.append(key)
        if None in config.values():
            _print_and_log(INVALID_CONFIG_FILE_MSG.format(**locals()))
            exit()
    else:
        logging.info("Using default program configuration settings:")
        if args.bashcomp or not args.no_log:  # only write when allowed to
            _print_and_log(("Writing default program configuration settings "
                            f"to {config_file}"))
            cfg[secn] = _str_dict(config)
            with open(config_file, 'w') as file:
                cfg.write(file)

    logging.info(config)

    return config


def _check_setting_fmt(setting_str):
    """Ensure proper setting format.  """
    with _handle_errors(err_types=AttributeError, msg=INVALID_SETTING_MSG):
        setting = re.search(f"(^{VALID_INPUT_SETTING}$)", setting_str).group(0)
    return setting


def _check_optn_fmt(optn_str):
    """Ensure proper option format.  """
    check_tag_option_re = re.compile(
        "^({mtag}*)({tag}+)({raw_opt})$".format(**GENERIC_RE_VARS))
    with _handle_errors(err_types=(AttributeError), msg=INVALID_OPTN_MSG):
        _, tag, raw_opt = check_tag_option_re.search(optn_str).groups()
    literal_tag = ''.join([rf'\{s}' for s in tag])  # read as literal
    return literal_tag, raw_opt


def _parse_and_check_input(args, config):
    """Parse input arguments. """
    InputDb = namedtuple('InputDb',
                         ['tag', 'raw_opt', 'setting', 'f_available',
                          'f_showfiles', 'f_bashcomp', 'rename_str',
                          'max_flines', 'max_fsize_kb', ])

    #  Check if renaming an option
    if args.rename == '':
        if args.setting == '' and not args.showfiles and not args.rename:
            args.available = True
    else:
        #  No setting, available, and showfiles arguments if renaming option
        if args.available:
            _print_and_log("Remove 'available' argument if renaming option.")
            exit()
        elif args.showfiles:
            _print_and_log("Remove 'showfiles' argument if renaming option.")
            exit()
        elif not args.setting == '':
            _print_and_log("Remove 'setting' argument if renaming option.")
            exit()

    if args.available or args.showfiles:
        tag_ = ANY_TAG
        raw_opt_ = ANY_RAW_OPTN
        setting_ = args.setting
        f_available_ = args.available
        f_showfiles_ = args.showfiles
    else:
        if args.rename == '':
            setting_ = _check_setting_fmt(args.setting)
        else:
            setting_ = ''
            _, _ = _check_optn_fmt(args.rename)

        tag_, raw_opt_ = _check_optn_fmt(args.option)
        f_available_ = False
        f_showfiles_ = False

    return InputDb(tag=tag_, raw_opt=raw_opt_, setting=setting_,
                   f_available=f_available_, f_showfiles=f_showfiles_,
                   f_bashcomp=args.bashcomp, rename_str=args.rename,
                   max_flines=config['max_flines'],
                   max_fsize_kb=config['max_fsize_kb'])


def optionset(args_arr):
    """Main optionset function. Input array of string arguments. """
    start_time = time()  # time program

    # Parse arguments
    args = parser.parse_args(args_arr)

    if args.help_full:
        parser.description = FULL_HELP_DESCRIPTION
        parser.print_help()
        return True

    if args.version:
        print(f"{BASENAME} {__version__}")
        return True

    # Reset global variables based on user input
    global g_f_quiet, g_f_verbose
    g_f_quiet = args.quiet
    g_f_verbose = args.verbose if not g_f_quiet else False

    # Set up logging
    args.aux_dir = Path(args.aux_dir)
    log_lvl = 'DEBUG' if args.debug else 'INFO'
    if args.no_log:
        log_path = Path(os.devnull)
    else:
        args.aux_dir.mkdir(parents=True, exist_ok=True)
        log_path = args.aux_dir / LOG_NAME
        if Path.exists(log_path):  # use unlink(missing_ok=True) if Python 3.8
            log_path.unlink()
    log_format = "%(levelname)s:%(message)s"
    logging.basicConfig(filename=log_path, level=log_lvl, format=log_format)

    # Run algorithm
    logging.info("Executing main optionset function")

    logging.info("Checking input options")
    logging.debug(f"args = {args}")
    config = _load_program_settings(args)
    input_db = _parse_and_check_input(args, config)
    logging.info(f"<tag><raw_opt> <setting> = "
                 f"{input_db.tag}{input_db.raw_opt} {input_db.setting}")

    logging.info("Generating valid files")
    valid_files = list(_gen_valid_files(config['ignore_files'],
                                        config['ignore_dirs']))
    logging.info(f"Valid files: {[str(vf) for vf in valid_files]}")

    optns_settings_db, var_optns_values_db, show_files_db, f_changes_made \
        = _scroll_through_files(valid_files, input_db=input_db)

    if args.available or args.showfiles:
        glob_pat = '*' if args.option is None else f"{args.option}*"
        _print_available(optns_settings_db, var_optns_values_db,
                         show_files_db, glob_pat, args.available)

    if args.bashcomp:
        _write_bashcompletion_file(optns_settings_db, var_optns_values_db,
                                   bashcomp_path=args.aux_dir/BASHCOMP_NAME)

    if f_changes_made and g_f_verbose:
        _print_and_log(f"See all modifications in {log_path}")

    total_prog_time = time() - start_time
    total_prog_time_msg = f"Finished in {total_prog_time:1.5f} s"
    if g_f_verbose:
        _print_and_log(total_prog_time_msg)
    else:
        logging.info(total_prog_time_msg)

    return True


def main():
    """Main function. """
    args_arr = argv[1:] if len(argv) > 1 else [""]
    optionset(args_arr)


# ############################################################ #
# Run main function
# ############################################################ #
if __name__ == '__main__':
    main()
