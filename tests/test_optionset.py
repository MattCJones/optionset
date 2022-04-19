#!/usr/bin/env python3
"""
Run unit tests on Optionset utility. See -h for help and -v for verbose.

Author: Matthew C. Jones
Email: matt.c.jones.aoe@gmail.com

:copyright: 2020 by Optionset authors, see AUTHORS for more details.
:license: GPLv3, see LICENSE for more details.
"""
import os
import re
import shlex
import shutil
import sys
import time
import unittest

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from subprocess import run, PIPE, STDOUT

from optionset.optionset import optionset, LOG_NAME, MAX_FLINES, MAX_FSIZE_KB

THIS_DIR = Path(__file__).parent
TEST_DIR = THIS_DIR
# TEST_DIR = Path(pkg_resources.resource_filename('optionset', "tests"))
AUX_DIR = TEST_DIR / "customAuxDir"
BASENAME = "optionset.py"
BIN_PATH = Path("optionset")  # command-line interface must be in PATH
RUN_APP = f"{BIN_PATH} --auxiliary-dir={AUX_DIR}"
LOG_PATH = AUX_DIR / LOG_NAME
CONFIG_PATH = AUX_DIR / "optionset.cfg"
BASHCOMP_PATH = AUX_DIR / "bash_completion"
FILES_TO_TEST_DIR = TEST_DIR / "filesToTest"
ARCHIVE_DIR = TEST_DIR / "archive"
SOL_DIR_A = ARCHIVE_DIR / "solSetA"
SOL_DIR_B = ARCHIVE_DIR / "solSetB"
SOL_DIR_C = ARCHIVE_DIR / "solSetC"
SOL_DIR_D = ARCHIVE_DIR / "solSetD"

# Uncomment to test manually and without installing:
# sys.path.append(TEST_DIR / '../optionset')
# from optionset.optionset import optionset, MAX_FLINES, MAX_FSIZE_KB
# BIN_PATH = TEST_DIR / "../optionset" / BASENAME


def ut_print(*args, **kwargs):
    """Print that takes into account verbosity level of test suite. """
    if ('-v' in sys.argv) or ('--verbose' in sys.argv):
        print(*args, **kwargs)


def test_regex(regex, str_to_search):
    """Test that regex expression works for given str_to_search. """
    if regex.search(str_to_search):
        return True
    return False


def run_cmd(cmd_str, check=True):
    """Run a command and return the output. """
    subproc = run(shlex.split(cmd_str), capture_output=False, stdout=PIPE,
                  stderr=STDOUT, check=check)
    output_str = subproc.stdout.decode('UTF-8')
    return output_str, subproc.returncode


def imported_optionset(input_arr):
    """Run optionset function imported from module. """
    input_arr.append("--auxiliary-dir")
    input_arr.append(str(AUX_DIR))
    optionset(input_arr)


def enable_testset_a():
    """Enable Test Set A. """
    opset_strs = ("@multiFile multiLine",
                  "@nestedL0 a",
                  "@nestedL1 a",
                  "@nestedL2 a",
                  "@overlappingMultiline a",
                  "@overlappingOption a",
                  "@overlappingOptionShort a",
                  "@valid0Dir a",
                  "@validCommentType Bash",
                  "@validExtension dat",
                  "@validSyntax difficultComments",
                  "~@$^multipleTags a",
                  "@nestedVarOp ' -12.34e-5'",
                  "@variableOption ' -81.2e-2'",
                  )
    for def_option_str in opset_strs:
        _, _ = run_cmd(f"{RUN_APP} {def_option_str}")


def enable_testset_b():
    """Enable Test Set B. """
    opset_strs = ("@multiFile singleLine",
                  "@nestedL0 b",
                  "@nestedL1 b",
                  "@nestedL2 b",
                  "@overlappingMultiline b",
                  "@overlappingOption b",
                  "@overlappingOptionShort b",
                  "@valid0Dir b",
                  "@validCommentType CPP",
                  "@validExtension nml",
                  "@validSyntax difficultLine",
                  "~@$^multipleTags b",
                  "@nestedVarOp 'eleventy two'",
                  "@variableOption '112'",
                  )
    for def_option_str in opset_strs:
        _, _ = run_cmd(f"{RUN_APP} {def_option_str}")


def enable_testset_c():
    """Enable Test Set C. """
    opset_strs = ("@multiFile multiLine",
                  "@nestedL0 b",
                  "@nestedL1 a",
                  "@nestedL2 b",
                  "@overlappingMultiline c",
                  "@overlappingOption c",
                  "@overlappingOptionShort c",
                  "@valid0Dir a",
                  "@validCommentType custom",
                  "@validExtension none",
                  "@validSyntax difficultComments",
                  "~@$^multipleTags a",
                  "@nestedVarOp ' -+ intermediate C 12.34e-5'",
                  "@variableOption ' -+ 12.34e-5 C'",
                  )
    for def_option_str in opset_strs:
        _, _ = run_cmd(f"{RUN_APP} {def_option_str}")


def enable_testset_d():
    """Enable Test Set D. """
    opset_strs = ("@multiFile multiLine",
                  "@nestedL0 a",
                  "@nestedL1 b",
                  "@nestedL2 none",
                  "@overlappingMultiline c",
                  "@overlappingOption c",
                  "@overlappingOptionShort c",
                  "@valid0Dir a",
                  "@validCommentType custom",
                  "@validExtension none",
                  "@validSyntax difficultComments",
                  "~@$^multipleTags a",
                  "@nestedVarOp ' -+ intermediate D 12.34e-5'",
                  "@variableOption ' -+ 12.34e-5 D'",
                  ("@rename var1 --rename-option $~@tempRename "
                   "--rename-setting VAR1"),
                  )
    for def_option_str in opset_strs:
        _, _ = run_cmd(f"{RUN_APP} {def_option_str}")

    opset_strs = ("@nestedL0 a",
                  "@nestedL1 b",
                  "@nestedL2 a",
                  "@overlappingOption a",
                  "@overlappingMultiline b",
                  "@overlappingOptionShort none",
                  "@nestedVarOp 'D -12.34E-5'",
                  ("$~@tempRename VAR1 --rename-option @rename "
                   "--rename-setting var1"),
                  )
    for def_option_str in opset_strs:
        _, _ = run_cmd(f"{RUN_APP} {def_option_str}")


def enable_default_options():
    """Set default options. """
    enable_testset_a()


@unittest.skipIf(False, "Skipping for debug")
class TestIO(unittest.TestCase):
    """Test program through input and output. """

    @classmethod
    def setUpClass(cls):
        ut_print(f"Changing to directory: {TEST_DIR}")
        os.chdir(TEST_DIR)
        ut_print("\nChecking proper input and output")
        ut_print("Resetting options")
        enable_default_options()

    @classmethod
    def tearDownClass(cls):
        ut_print("\nResetting options")
        enable_default_options()

    ############################################################
    # Test basic
    ############################################################
    def test_basic_io(self):
        """Test basic input and output. """
        re_str = r".*InputError.*[\r\n].*Invalid option name.*"
        re_has_input_err = re.compile(re_str)
        output_str, _ = run_cmd(f"{RUN_APP} @invalid@Option validSetting")
        self.assertTrue(test_regex(re_has_input_err, output_str),
                        msg=f"SHOULD MATCH: {re_str}:\nAND: {output_str}")

        re_str = r".*InputError.*[\r\n].*Invalid setting name.*"
        re_has_input_err = re.compile(re_str)
        output_str, _ = run_cmd(f"{RUN_APP} @validOption @invalidSetting")
        self.assertTrue(test_regex(re_has_input_err, output_str),
                        msg="Invalid setting")

        re_shows_usage = re.compile("^usage:.*")
        output_str, _ = run_cmd(f"{RUN_APP} -h")
        self.assertTrue(test_regex(re_shows_usage, output_str))

    def test_ignored(self):
        """Test ignored files and directories. """
        re_has_ignore_str = re.compile(".*shouldIgnore.*")
        output_str, _ = run_cmd(f"{RUN_APP} -a")
        self.assertFalse(test_regex(re_has_ignore_str, output_str),
                         msg=(f"SHOULD NOT MATCH: {re_has_ignore_str}\nAND: "
                              f"{output_str}"))

    def test_extensions(self):
        """Test various valid file extensions. """
        output_str, _ = run_cmd(f"{RUN_APP} -a @validExtension")
        setting_strs = ('dat', 'nml', 'none', 'txt', 'org', 'orig', 'yaml',)
        for setting_str in setting_strs:
            re_has_extension = re.compile(f".*{setting_str}.*")
            self.assertTrue(test_regex(re_has_extension, output_str))

    def test_showfiles(self):
        """Test functionality to show files of available options. """
        match_str = ".*"\
            + r"filesToTest/validSyntax/difficultCommentPlacement\.dat "\
            + r"filesToTest/validSyntax/multilineOption\.dat "\
            + r"filesToTest/validSyntax/validSyntax\.dat" + os.linesep\
            + "------------------------------------------------------------"
        re_has_file_paths_str = re.compile(match_str)
        output_str, _ = run_cmd(f"{RUN_APP} @validSyntax -f")
        self.assertTrue(test_regex(re_has_file_paths_str, output_str),
                        msg=f"SHOULD MATCH:\n{re_has_file_paths_str}\nAND:\n"
                            f"{output_str}")

    ############################################################
    # Test Python import functionality
    ############################################################
    def test_python_import(self):
        """Test that same output is found using both command line and Python
        import functionality. """
        cmd_line_output_str, _ = run_cmd(f"{RUN_APP} @val -a")
        f_io = StringIO()
        with redirect_stdout(f_io):  # capture standard out
            imported_optionset(["@val", "-a"])
        py_import_output_str = f_io.getvalue()
        self.assertEqual(cmd_line_output_str, py_import_output_str)

    ############################################################
    # Test invalid format
    ############################################################
    def test_invalid(self):
        """Test invalid files and directories. """
        re_invalid = re.compile(".*ERROR.*")
        output_str, _ = run_cmd(f"{RUN_APP} -a")
        self.assertFalse(test_regex(re_invalid, output_str))

    ############################################################
    # Test valid format
    ############################################################
    def test_comment_types(self):
        """Test various comment types. """
        output_str, _ = run_cmd(f"{RUN_APP} -a @validCommentType")
        setting_strs = ('Bash', 'CPP', 'MATLAB', 'NML', 'custom',)
        for setting_str in setting_strs:
            re_comment_type = re.compile(f".*{setting_str}.*")
            self.assertTrue(test_regex(re_comment_type, output_str))

    def test_valid_syntax(self):
        """Test proper syntax of options and settings. """
        output_str, _ = run_cmd(f"{RUN_APP} -a @validSyntax")
        setting_strs = ('difficultPlacement', 'multiline', 'difficultLine',
                        'difficultComment',)
        for setting_str in setting_strs:
            re_syntax = re.compile(f".*{setting_str}.*")
            self.assertTrue(test_regex(re_syntax, output_str))

    def test_variable_options(self):
        """Test variable option. """
        var_setting_str = '1e-8'
        re_setting = re.compile(f".*{var_setting_str}.*")

        output_str_before, _ = run_cmd(f"{RUN_APP} -a @variableOption")
        self.assertFalse(test_regex(re_setting, output_str_before))

        run_str = f"{RUN_APP} -v @variableOption {var_setting_str}"
        output_str_change, _ = run_cmd(run_str)
        self.assertTrue(test_regex(re_setting, output_str_change))

        output_str_after, _ = run_cmd(f"{RUN_APP} -a @variableOption")
        self.assertTrue(test_regex(re_setting, output_str_after))

    def test_multiple_tags(self):
        """Test multiple tags in options. """
        option_str = r"~@$^multipleTags"
        output_str, _ = run_cmd(f"{RUN_APP} -a {option_str}")
        re_syntax = re.compile(r".*\~\@\$\^multipleTags.*")
        self.assertTrue(test_regex(re_syntax, output_str))

    def test_multiple_files(self):
        """Test options placed in multiple files. """
        option_str = r"\@multiFile"

        setting_str = "singleLine"
        output_str, _ = run_cmd(f"{RUN_APP} {option_str} {setting_str} -v")
        re_multi_file_single_line = re.compile(
            f".*{option_str} {setting_str}.*")
        self.assertTrue(test_regex(re_multi_file_single_line, output_str))

        setting_str = "multiLine"
        output_str, _ = run_cmd(f"{RUN_APP} {option_str} {setting_str} -v")
        re_multi_file_multi_line = re.compile(
            f".*{option_str} {setting_str}.*")
        self.assertTrue(test_regex(re_multi_file_multi_line, output_str))

    def test_overlapping_options(self):
        """Test overlapping options. """
        # Standard overlapping option
        option_str = r"\@overlappingOption"
        setting_str = "c"
        output_str, _ = run_cmd(f"{RUN_APP} {option_str} {setting_str} -v")
        re_overlapping = re.compile(f".*{option_str} {setting_str}.*")
        self.assertTrue(test_regex(re_overlapping, output_str))

        output_str, _ = run_cmd(f"{RUN_APP} {option_str} -a")
        re_overlapping = re.compile(f".*> {setting_str} <.*")
        self.assertTrue(test_regex(re_overlapping, output_str))

        setting_str = "b"
        output_str, _ = run_cmd(f"{RUN_APP} {option_str} {setting_str} -v")
        re_overlapping = re.compile(f".*{option_str} {setting_str}.*")
        self.assertTrue(test_regex(re_overlapping, output_str))

        output_str, _ = run_cmd(f"{RUN_APP} {option_str} -a")
        re_overlapping = re.compile(f".*> {setting_str} <.*")
        self.assertTrue(test_regex(re_overlapping, output_str))

        # Short overlapping option
        option_str = r"\@overlappingOptionShort"
        setting_str = "c"
        output_str, _ = run_cmd(f"{RUN_APP} {option_str} {setting_str} -v")
        re_overlapping_short = re.compile(f".*{option_str} {setting_str}.*")
        self.assertTrue(test_regex(re_overlapping_short, output_str))

        output_str, _ = run_cmd(f"{RUN_APP} {option_str} -a")
        re_overlapping_short = re.compile(f".*> {setting_str} <.*")
        self.assertTrue(test_regex(re_overlapping_short, output_str))

        # Overlapping multiline options
        option_str = r"\@overlappingMultiline"
        setting_str = "c"
        output_str, _ = run_cmd(f"{RUN_APP} {option_str} {setting_str} -v")
        re_overlapping_multiline = re.compile(
            f".*{option_str} {setting_str}.*")
        self.assertTrue(test_regex(re_overlapping_multiline, output_str))

        output_str, _ = run_cmd(f"{RUN_APP} {option_str} -a")
        re_overlapping_multiline = re.compile(f".*> {setting_str} <.*")
        self.assertTrue(test_regex(re_overlapping_multiline, output_str))

        setting_str = "b"
        output_str, _ = run_cmd(f"{RUN_APP} {option_str} {setting_str} -v")
        re_overlapping_multiline = re.compile(
            f".*{option_str} {setting_str}.*")
        self.assertTrue(test_regex(re_overlapping_multiline, output_str))

        output_str, _ = run_cmd(f"{RUN_APP} {option_str} -a")
        re_overlapping_multiline = re.compile(f".*> {setting_str} <.*")
        self.assertTrue(test_regex(re_overlapping_multiline, output_str))

    def test_nested_options(self):
        """Test multi-scoped options. """
        option_str = r"\@nested"
        output_str, _ = run_cmd(f"{RUN_APP} {option_str} -a")

        option_str = r"\@nestedL0"
        re_nested = re.compile(f".*{option_str}.*")
        self.assertTrue(test_regex(re_nested, output_str))

        option_str = r"\@nestedL1"
        re_nested = re.compile(f".*{option_str}.*")
        self.assertTrue(test_regex(re_nested, output_str))

        option_str = r"\@nestedL2"
        re_nested = re.compile(f".*{option_str}.*")
        self.assertTrue(test_regex(re_nested, output_str))

        option_str = r"\@nestedVarOp"
        re_nested = re.compile(f".*{option_str}.*")
        self.assertTrue(test_regex(re_nested, output_str))

        option_str = r"\@nestedVarOp"
        setting_str = r" 8.23e-3"
        output_str, _ = run_cmd(f"{RUN_APP} {option_str} {setting_str} -v")
        re_nested = re.compile(f".*{setting_str}.*{option_str}.*")
        self.assertTrue(test_regex(re_nested, output_str))

    ############################################################
    # Test auxiliary directory files
    ############################################################
    def test_bash_completion(self):
        """Test that Bash completion file is properly written. """
        _, _ = run_cmd(f"rm -f {CONFIG_PATH}")
        _, _ = run_cmd(f"{RUN_APP} @none none --bash-completion")
        with open(BASHCOMP_PATH, 'r') as file:
            bash_comp_str = file.read()
        short_opts = "'-H' '-a' '-d' '-f' '-h' '-n' '-q' '-v'"
        long_opts = ("'--available' '--bash-completion' '--debug' '--help' "
                     "'--help-full' '--help-full' '--no-log' '--quiet' "
                     "'--rename-option' '--rename-setting' '--show-files' "
                     "'--verbose' '--version'")
        bash_comp_re_str = rf"""#!/bin/bash
# Auto-generated Bash completion settings for optionset.py
# Run 'source [a-zA-Z\/\\ ]*customAuxDir/bash_completion' to enable
.*
\s*{short_opts}
\s*{long_opts}
.*
complete -F _optionset os
complete -F _optionset optionset"""
        re_match = re.compile(bash_comp_re_str, re.DOTALL)
        self.assertTrue(test_regex(re_match, bash_comp_str),
                        msg=f"SHOULD MATCH:\n{re_match}\nAND:\n{bash_comp_str}"
                        )

    def test_config_file(self):
        """Test that configuration file is properly written. """
        _, _ = run_cmd(f"rm -f {CONFIG_PATH}")
        _, _ = run_cmd(f"{RUN_APP} @none none ")
        with open(CONFIG_PATH, 'r') as file:
            cfg_str = file.read()
        cfg_re_str = rf"""\[Files\]
ignore_dirs = .*
ignore_files = .*
max_flines = {MAX_FLINES}
max_fsize_kb = {MAX_FSIZE_KB}"""
        re_match = re.compile(cfg_re_str)
        self.assertTrue(test_regex(re_match, cfg_str))

    ############################################################
    # Regression test: show that output is unchanged in new version
    ############################################################
    def test_log_output(self):
        """Regression test: show that output is unchanged in new version"""
        _, _ = run_cmd(f"{RUN_APP} @none none")
        with open(LOG_PATH, 'r') as file:
            log_str = file.read()
        log_re_str = r"""INFO:Executing main optionset function
INFO:Checking input options
INFO:Reading program settings from [a-zA-Z\/\\ ]+/optionset.cfg:
INFO:\{.*\}
INFO:<tag><raw_opt> <setting> = \\@none none
INFO:Generating valid files
INFO:Valid files: \[.*\]
INFO:Scrolling through files to set: \\@none none
INFO:Skipping: test_optionset.py
\s+File exceeds kB size limit of 10
INFO:Skipping: filesToTest/shouldIgnore/binaryFile.dat
\s+'utf-8' codec can't decode byte 0xd9 in position 8:.*
INFO:Skipping: filesToTest/shouldIgnore/binaryFile.dat
\s+'utf-8' codec can't decode byte 0xd9 in position 8:.*
INFO:Skipping: filesToTest/shouldIgnore/binaryFile.dat
\s+'utf-8' codec can't decode byte 0xd9 in position 8:.*
INFO:Skipping: filesToTest/shouldIgnore/tooLarge10kB.dat
\s+File exceeds kB size limit of 10
INFO:Skipping: filesToTest/shouldIgnore/tooManyLines.dat
\s+File exceeds kB size limit of 10
INFO:Finished in \d+.\d+ s"""
        re_regression_match = re.compile(log_re_str)
        self.assertTrue(test_regex(re_regression_match, log_str),
                        msg=f"SHOULD MATCH:\n{re_regression_match}\nAND:\n"
                            f"{log_str}\n\nLOG_PATH={LOG_PATH}\n"
                            f"RUN_APP={RUN_APP}")

    ############################################################
    # Test renaming of options and settings
    ############################################################
    def test_rename(self):
        """Test renaming of options and settings. """

        # Rename just option
        _, _ = run_cmd(f"{RUN_APP} @rename --rename-option @RENAME")
        output_str, _ = run_cmd(f"{RUN_APP} @RENAME -a")
        rename_re_str = r"@RENAME"
        re_match = re.compile(rename_re_str, re.DOTALL)
        self.assertTrue(test_regex(re_match, output_str))
        # Reset
        _, _ = run_cmd(f"{RUN_APP} @RENAME --rename-option @rename")
        output_str, _ = run_cmd(f"{RUN_APP} @rename -a")
        rename_re_str = r"@rename"
        re_match = re.compile(rename_re_str, re.DOTALL)
        self.assertTrue(test_regex(re_match, output_str))

        # Rename just setting
        _, _ = run_cmd(f"{RUN_APP} @rename var1 --rename-setting VAR1")
        output_str, _ = run_cmd(f"{RUN_APP} @rename -a")
        rename_re_str = r"VAR1"
        re_match = re.compile(rename_re_str, re.DOTALL)
        self.assertTrue(test_regex(re_match, output_str))
        # Reset
        _, _ = run_cmd(f"{RUN_APP} @rename VAR1 --rename-setting var1")
        output_str, _ = run_cmd(f"{RUN_APP} @rename -a")
        rename_re_str = r"var1"
        re_match = re.compile(rename_re_str, re.DOTALL)
        self.assertTrue(test_regex(re_match, output_str))

        # Rename option and setting
        cmd_str = (f"{RUN_APP} @rename var1 --rename-option @RENAME "
                   f"--rename-setting VAR1")
        _, _ = run_cmd(cmd_str)
        output_str, _ = run_cmd(f"{RUN_APP} @RENAME -a")
        rename_re_str = r"@RENAME.*VAR1"
        re_match = re.compile(rename_re_str, re.DOTALL)
        self.assertTrue(test_regex(re_match, output_str))
        # Reset
        cmd_str = (f"{RUN_APP} @RENAME VAR1 --rename-option @rename "
                   f"--rename-setting var1")
        _, _ = run_cmd(cmd_str)
        output_str, _ = run_cmd(f"{RUN_APP} @rename -a")
        rename_re_str = r"@rename.*var1"
        re_match = re.compile(rename_re_str, re.DOTALL)
        self.assertTrue(test_regex(re_match, output_str))


@unittest.skipIf(False, "Skipping test sets")
class TestSets(unittest.TestCase):
    """Run through Test Sets and verify output. """

    checkDiffMsg = "Differences in files shown above."

    @classmethod
    def setUpClass(cls):
        ut_print("\nChecking all test sets")
        ut_print(f"Changing to directory: {TEST_DIR}")
        os.chdir(TEST_DIR)

    @classmethod
    def tearDownClass(cls):
        ut_print("\nResetting options")
        enable_default_options()

    @unittest.skipIf(not os.path.exists(SOL_DIR_A), f"No dir: {SOL_DIR_A}")
    def testset_a(self):
        """Test Set A (default). """
        ut_print("\nEnabling Test Set A")
        enable_testset_a()
        output_str, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_A}",
                                check=False)
        self.assertEqual(output_str, "", msg=self.checkDiffMsg)

    @unittest.skipIf(not os.path.exists(SOL_DIR_B), f"No dir: {SOL_DIR_B}")
    def testset_b(self):
        """Test Set B. """
        ut_print("\nEnabling Test Set B")
        enable_testset_b()
        output_str, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_B}",
                                check=False)
        self.assertEqual(output_str, "", msg=self.checkDiffMsg)

    @unittest.skipIf(not os.path.exists(SOL_DIR_C), f"No dir: {SOL_DIR_C}")
    def testset_c(self):
        """Test Set C. """
        ut_print("\nEnabling Test Set C")
        enable_testset_c()
        output_str, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_C}",
                                check=False)
        self.assertEqual(output_str, "", msg=self.checkDiffMsg)

    @unittest.skipIf(not os.path.exists(SOL_DIR_D), f"No dir: {SOL_DIR_D}")
    def testset_d(self):
        """Test Set D. """
        ut_print("\nEnabling Test Set D")
        enable_testset_d()
        output_str, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_D}",
                                check=False)
        self.assertEqual(output_str, "", msg=self.checkDiffMsg)


def mkdirs(dir_str):
    """Make directory if it does not exist. """
    if not os.path.exists(dir_str):
        os.makedirs(dir_str)


def mvdir_to_trash(dir_str):
    """Move a directory to trash/ ; rename if necessary. """
    if not os.path.exists(dir_str):
        return
    trash_dir = "trash"
    to_dir = f"{trash_dir}/{dir_str}"
    while os.path.exists(to_dir):
        re_to_dir = re.compile(r"([a-zA-Z\-]+)_(\d+)")
        search_to_dir = re_to_dir.search(to_dir)
        if search_to_dir:
            idx = int(search_to_dir.group(2))
            idx += 1
            to_dir = f"{trash_dir}/{search_to_dir.group(1)}_{idx}"
        else:
            to_dir = f"{trash_dir}/{dir_str}_0"

    mkdirs(trash_dir)
    print(f"Moving {dir_str} to {to_dir}")
    shutil.move(dir_str, to_dir)


def generate_solution_sets():
    """Generation solution test sets that are compared to with diff utility.
    """
    ut_print(f"Changing to directory: {TEST_DIR}")
    os.chdir(TEST_DIR)

    mvdir_to_trash(ARCHIVE_DIR)
    mkdirs(ARCHIVE_DIR)

    print("Generating solution set A")
    enable_testset_a()
    shutil.copytree(FILES_TO_TEST_DIR, SOL_DIR_A)

    print("Generating solution set B")
    enable_testset_b()
    shutil.copytree(FILES_TO_TEST_DIR, SOL_DIR_B)

    print("Generating solution set C")
    enable_testset_c()
    shutil.copytree(FILES_TO_TEST_DIR, SOL_DIR_C)

    print("Generating solution set D")
    enable_testset_d()
    shutil.copytree(FILES_TO_TEST_DIR, SOL_DIR_D)

    print("Resetting options")
    enable_default_options()


@unittest.skipIf(False, "Skipping time test")
class TestRuntime(unittest.TestCase):
    """Benchmark how long it takes to run the code. """

    @classmethod
    def setUpClass(cls):
        ut_print("\nBenchmarking run time")
        ut_print(f"Changing to directory: {TEST_DIR}")
        os.chdir(TEST_DIR)

    @classmethod
    def tearDownClass(cls):
        ut_print("\nResetting options")
        enable_default_options()

    @unittest.skipIf(not os.path.exists(SOL_DIR_A), f"No dir: {SOL_DIR_A}")
    def testset_a(self):
        """Test Set A (default). """

        runtimes = []
        N = 10
        for i in range(N):
            start_time = time.time()
            output_str, _ = run_cmd(f"{BIN_PATH} -q @op 2")
            this_time = time.time() - start_time
            runtimes.append(this_time)
            ut_print("Time [s]: {:1.5f}".format(this_time))

        # Compute mean run time
        sum = 0
        for runtime in runtimes:
            sum += runtime
        runtime_mean = sum/len(runtimes)

        ut_print("Avg run time [s]: {:1.5f}".format(runtime_mean))

        runtime_allowable = 0.4  # seconds
        self.assertLess(runtime_mean, runtime_allowable,
                        msg=("Mean run time of {runtime_mean:.2f) s is lower "
                             f"than allowable of {runtime_allowable:.2f} s."))


def main():
    """Main function """
    F_help = '-h' in sys.argv or '--help' in sys.argv
    F_generate = '-g' in sys.argv or '--generate' in sys.argv

    if F_help:
        scriptName = os.path.basename(__file__)
        print("------------------------------------------------------------")
        print(f"usage: {scriptName} [-g] [--generate] "
              f"to generate solution sets")
        print("---------------------------- or ----------------------------")
        return

    if F_generate:
        generate_solution_sets()
    else:  # run tests as normal
        unittest.main()


if __name__ == '__main__':
    main()
