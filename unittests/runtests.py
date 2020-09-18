#!/usr/bin/env python3
"""
Run unit tests on Optionset utility. See -h for help and -v for verbose.

Author: Matthew C. Jones
Email: matt.c.jones.aoe@gmail.com

:copyright: 2020 by Optionset authors, see AUTHORS for more details.
:license: GPLv3, see LICENSE for more details.
"""
import unittest
import os
import re
import shlex
import shutil
import subprocess
import sys

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from time import time

sys.path.append('../optionset')
from optionset import optionset, MAX_FLINES, MAX_FSIZE_KB

AUX_DIR = Path("customAuxDir")
BASENAME = "optionset.py"
BIN_PATH = Path("../optionset") / BASENAME
RUN_APP = f"{BIN_PATH} --auxillary-dir={AUX_DIR}"
LOG_PATH = AUX_DIR / f"log.{BASENAME}"
CONFIG_PATH = AUX_DIR / "optionset.cfg"
BASHCOMP_PATH = AUX_DIR / "bash_completion"
FILES_TO_TEST_DIR = "filesToTest"
ARCHIVE_DIR = Path("archive")
SOL_DIR_A = ARCHIVE_DIR / "solSetA"
SOL_DIR_B = ARCHIVE_DIR / "solSetB"
SOL_DIR_C = ARCHIVE_DIR / "solSetC"
SOL_DIR_D = ARCHIVE_DIR / "solSetD"

F_skipTestSets = False


def ut_print(*args, **kwargs):
    """Print that takes into account verbosity level of test suite. """
    if ('-v' in sys.argv) or ('--verbose' in sys.argv):
        print(*args, **kwargs)


def test_regex(regex, strToSearch):
    """Test that regex expression works for given strToSearch. """
    if regex.search(strToSearch):
        return True
    else:
        return False


def run_cmd(cmdStr, check=True):
    """Run a command and return the output. """
    subproc = subprocess.run(shlex.split(cmdStr), capture_output=True,
                             check=check)
    outputStr = subproc.stdout.decode('UTF-8')
    return outputStr, subproc.returncode


def imported_optionset(*args, **kwargs):
    """Run optionset function imported from module. """
    inputArr = [*args]
    inputArr.append("--auxillaryDir")
    inputArr.append(AUX_DIR)
    optionset(*args, **kwargs)


def enable_testset_a():
    """Enable Test Set A. """
    opSetStrs = (
            "@multiFile multiLine",
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
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUN_APP} {defOptionStr}")


def enable_testset_b():
    """Enable Test Set B. """
    opSetStrs = (
            "@multiFile singleLine",
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
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUN_APP} {defOptionStr}")


def enable_testset_c():
    """Enable Test Set C. """
    opSetStrs = (
            "@multiFile multiLine",
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
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUN_APP} {defOptionStr}")


def enable_testset_d():
    """Enable Test Set D. """
    opSetStrs = (
            "@multiFile multiLine",
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
            )
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUN_APP} {defOptionStr}")

    opSetStrs = (
            "@nestedL0 a",
            "@nestedL1 b",
            "@nestedL2 a",
            "@overlappingOption a",
            "@overlappingMultiline b",
            "@overlappingOptionShort none",
            "@nestedVarOp 'D -12.34E-5'",
            )
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUN_APP} {defOptionStr}")


def enable_default_options():
    """Set default options. """
    enable_testset_a()


@unittest.skipIf(False, "Skipping for debug")
class TestIO(unittest.TestCase):
    """Test program through input and output. """

    def setUp(self):
        """Run before tests. """
        pass

    def tearDown(self):
        """Run after tests. """
        pass

    @classmethod
    def setUpClass(cls):
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
        reStr = r".*InputError.*[\r\n].*Invalid option name.*"
        reHasInputErr = re.compile(reStr)
        outputStr, _ = run_cmd(f"{RUN_APP} @invalid@Option validSetting")
        self.assertTrue(test_regex(reHasInputErr, outputStr),
                        "Invalid option")

        reStr = r".*InputError.*[\r\n].*Invalid setting name.*"
        reHasInputErr = re.compile(reStr)
        outputStr, _ = run_cmd(f"{RUN_APP} @validOption @invalidSetting")
        self.assertTrue(test_regex(reHasInputErr, outputStr),
                        msg="Invalid setting")

        reShowsUsage = re.compile("^usage:.*")
        outputStr, _ = run_cmd(f"{RUN_APP} -h")
        self.assertTrue(test_regex(reShowsUsage, outputStr))

    def test_ignored(self):
        """Test ignored files and directories. """
        reHasIgnoreStr = re.compile(".*shouldIgnore.*")
        outputStr, _ = run_cmd(f"{RUN_APP} -a")
        self.assertFalse(test_regex(reHasIgnoreStr, outputStr))

    def test_extensions(self):
        """Test various valid file extensions. """
        outputStr, _ = run_cmd(f"{RUN_APP} -a @validExtension")
        settingStrs = ('dat', 'nml', 'none', 'txt', 'org', 'orig', 'yaml',)
        for settingStr in settingStrs:
            reHasExtension = re.compile(f".*{settingStr}.*")
            self.assertTrue(test_regex(reHasExtension, outputStr))

    def test_showfiles(self):
        """Test functionality to show files of available options. """
        matchStr = ".*"\
            + r"filesToTest/validSyntax/difficultCommentPlacement\.dat "\
            + r"filesToTest/validSyntax/multilineOption\.dat "\
            + r"filesToTest/validSyntax/validSyntax\.dat" + os.linesep\
            + "------------------------------------------------------------"
        reHasFilePathsStr = re.compile(matchStr)
        outputStr, _ = run_cmd(f"{RUN_APP} @validSyntax -f")
        self.assertTrue(test_regex(reHasFilePathsStr, outputStr))

    ############################################################
    # Test Python import functionality
    ############################################################
    def test_python_import(self):
        """Test that same output is found using both command line and Python
        import functionality. """
        cmdLineOutputStr, _ = run_cmd(f"{RUN_APP} @val -a")
        fIO = StringIO()
        with redirect_stdout(fIO):  # capture standard out
            imported_optionset(["@val", "-a"])
        pyImportOutputStr = fIO.getvalue()
        self.assertEqual(cmdLineOutputStr, pyImportOutputStr)

    ############################################################
    # Test invalid format
    ############################################################
    def test_invalid(self):
        """Test invalid files and directories. """
        reInvalid = re.compile(".*ERROR.*")
        outputStr, _ = run_cmd(f"{RUN_APP} -a")
        self.assertFalse(test_regex(reInvalid, outputStr))

    ############################################################
    # Test valid format
    ############################################################
    def test_comment_types(self):
        """Test various comment types. """
        outputStr, _ = run_cmd(f"{RUN_APP} -a @validCommentType")
        settingStrs = ('Bash', 'CPP', 'MATLAB', 'NML', 'custom',)
        for settingStr in settingStrs:
            reCommentType = re.compile(f".*{settingStr}.*")
            self.assertTrue(test_regex(reCommentType, outputStr))

    def test_valid_syntax(self):
        """Test proper syntax of options and settings. """
        outputStr, _ = run_cmd(f"{RUN_APP} -a @validSyntax")
        settingStrs = ('difficultPlacement', 'multiline', 'difficultLine',
                       'difficultComment',)
        for settingStr in settingStrs:
            reSyntax = re.compile(f".*{settingStr}.*")
            self.assertTrue(test_regex(reSyntax, outputStr))

    def test_variable_options(self):
        """Test variable option. """
        varSettingStr = '1e-8'
        reSetting = re.compile(f".*{varSettingStr}.*")

        outputStrBefore, _ = run_cmd(f"{RUN_APP} -a @variableOption")
        self.assertFalse(test_regex(reSetting, outputStrBefore))

        runStr = f"{RUN_APP} -v @variableOption {varSettingStr}"
        outputStrChange, _ = run_cmd(runStr)
        self.assertTrue(test_regex(reSetting, outputStrChange))

        outputStrAfter, _ = run_cmd(f"{RUN_APP} -a @variableOption")
        self.assertTrue(test_regex(reSetting, outputStrAfter))

    def test_multiple_tags(self):
        """Test multiple tags in options. """
        optionStr = r"~@$^multipleTags"
        outputStr, _ = run_cmd(f"{RUN_APP} -a {optionStr}")
        reSyntax = re.compile(r".*\~\@\$\^multipleTags.*")
        self.assertTrue(test_regex(reSyntax, outputStr))

    def test_multiple_files(self):
        """Test options placed in multiple files. """
        optionStr = r"\@multiFile"

        settingStr = "singleLine"
        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} {settingStr} -v")
        reMultiFileSingleLine = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reMultiFileSingleLine, outputStr))

        settingStr = "multiLine"
        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} {settingStr} -v")
        reMultiFileMultiLine = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reMultiFileMultiLine, outputStr))

    def test_overlapping_options(self):
        """Test overlapping options. """
        # Standard overlapping option
        optionStr = r"\@overlappingOption"
        settingStr = "c"
        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} {settingStr} -v")
        reOverlapping = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reOverlapping, outputStr))

        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} -a")
        reOverlapping = re.compile(f".*> {settingStr} <.*")
        self.assertTrue(test_regex(reOverlapping, outputStr))

        settingStr = "b"
        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} {settingStr} -v")
        reOverlapping = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reOverlapping, outputStr))

        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} -a")
        reOverlapping = re.compile(f".*> {settingStr} <.*")
        self.assertTrue(test_regex(reOverlapping, outputStr))

        # Short overlapping option
        optionStr = r"\@overlappingOptionShort"
        settingStr = "c"
        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} {settingStr} -v")
        reOverlappingShort = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reOverlappingShort, outputStr))

        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} -a")
        reOverlappingShort = re.compile(f".*> {settingStr} <.*")
        self.assertTrue(test_regex(reOverlappingShort, outputStr))

        # Overlapping multiline options
        optionStr = r"\@overlappingMultiline"
        settingStr = "c"
        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} {settingStr} -v")
        reOverlappingMultiline = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reOverlappingMultiline, outputStr))

        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} -a")
        reOverlappingMultiline = re.compile(f".*> {settingStr} <.*")
        self.assertTrue(test_regex(reOverlappingMultiline, outputStr))

        settingStr = "b"
        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} {settingStr} -v")
        reOverlappingMultiline = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reOverlappingMultiline, outputStr))

        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} -a")
        reOverlappingMultiline = re.compile(f".*> {settingStr} <.*")
        self.assertTrue(test_regex(reOverlappingMultiline, outputStr))

    def test_nested_options(self):
        """Test multi-scoped options. """
        optionStr = r"\@nested"
        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} -a")

        optionStr = r"\@nestedL0"
        reNested = re.compile(f".*{optionStr}.*")
        self.assertTrue(test_regex(reNested, outputStr))

        optionStr = r"\@nestedL1"
        reNested = re.compile(f".*{optionStr}.*")
        self.assertTrue(test_regex(reNested, outputStr))

        optionStr = r"\@nestedL2"
        reNested = re.compile(f".*{optionStr}.*")
        self.assertTrue(test_regex(reNested, outputStr))

        optionStr = r"\@nestedVarOp"
        reNested = re.compile(f".*{optionStr}.*")
        self.assertTrue(test_regex(reNested, outputStr))

        optionStr = r"\@nestedVarOp"
        settingStr = r" 8.23e-3"
        outputStr, _ = run_cmd(f"{RUN_APP} {optionStr} {settingStr} -v")
        reNested = re.compile(f".*{settingStr}.*{optionStr}.*")
        self.assertTrue(test_regex(reNested, outputStr))

    ############################################################
    # Test auxillary directory files
    ############################################################
    def test_bash_completion(self):
        """Test that Bash completion file is properly written. """
        _, _ = run_cmd(f"rm -f {CONFIG_PATH}")
        outputStr, _ = run_cmd(f"{RUN_APP} @none none")
        with open(BASHCOMP_PATH, 'r') as file:
            bashCompStr = file.read()
        shortOpts = "'-H' '-a' '-d' '-f' '-h' '-n' '-q' '-v'"
        longOpts = ("'--available' '--bash-completion' '--debug' '--help' "
                    "'--help-full' '--help-full' '--no-log' '--quiet' "
                    "'--show-files' '--verbose' '--version'")
        bashCompReStr = rf"""#!/bin/bash
# Auto-generated Bash completion settings for optionset.py
# Run 'source customAuxDir/bash_completion' to enable
.*
\s*{shortOpts}
\s*{longOpts}
.*
complete -F _optionset os
complete -F _optionset optionset"""
        reRegressionMatch = re.compile(bashCompReStr, re.DOTALL)
        self.assertTrue(test_regex(reRegressionMatch, bashCompStr))

    def test_config_file(self):
        """Test that configuration file is properly written. """
        _, _ = run_cmd(f"rm -f {CONFIG_PATH}")
        outputStr, _ = run_cmd(f"{RUN_APP} @none none")
        with open(CONFIG_PATH, 'r') as file:
            cfgStr = file.read()
        cfgReStr = rf"""\[Files\]
ignoreDirs = .*
ignoreFiles = .*
maxFileLines = {MAX_FLINES}
maxFileSizeKb = {MAX_FSIZE_KB}"""
        reRegressionMatch = re.compile(cfgReStr)
        self.assertTrue(test_regex(reRegressionMatch, cfgStr))

    ############################################################
    # Regression test: show that output is unchanged in with new version
    ############################################################
    def test_log_output(self):
        """Regression test of log output. """
        outputStr, _ = run_cmd(f"{RUN_APP} @none none")
        with open(LOG_PATH, 'r') as file:
            logStr = file.read()
        logReStr = r"""INFO:Executing main optionset function
INFO:Checking input options
INFO:Reading program settings from \w+/optionset.cfg:
INFO:.*
INFO:<tag><rawOpt> <setting> = \\@none none
INFO:Generating valid files
INFO:Valid files: \[.*\]
INFO:Scrolling through files to set: \\@none none
WARNING:Skipping: filesToTest/shouldIgnore/binaryFile.dat
WARNING:Reason: 'utf-8' codec can't decode byte .* in position \d+:.*
WARNING:Skipping: filesToTest/shouldIgnore/binaryFile.dat
WARNING:Reason: 'utf-8' codec can't decode byte .* in position \d+:.*
WARNING:Skipping: filesToTest/shouldIgnore/binaryFile.dat
WARNING:Reason: 'utf-8' codec can't decode byte .* in position \d+:.*
WARNING:Skipping: filesToTest/shouldIgnore/tooLarge10kB.dat
WARNING:Reason: File exceeds kB size limit of 10
WARNING:Skipping: filesToTest/shouldIgnore/tooManyLines.dat
WARNING:Reason: File exceeds kB size limit of 10
INFO:Finished in \d+.\d+ s"""
        reRegressionMatch = re.compile(logReStr)
        self.assertTrue(test_regex(reRegressionMatch, logStr))


@unittest.skipIf(F_skipTestSets, "Skipping test sets")
class TestSets(unittest.TestCase):
    """Run through Test Sets and verify output. """

    checkDiffMsg = "Differences in files shown below:\n{diffOutput}"

    def setUp(self):
        """Run before tests. """
        pass

    def tearDown(self):
        """Run after tests. """
        pass

    @classmethod
    def setUpClass(cls):
        ut_print("\nChecking all test sets")

    @classmethod
    def tearDownClass(cls):
        ut_print("\nResetting options")
        enable_default_options()

    @unittest.skipIf(not os.path.exists(SOL_DIR_A), f"No dir: {SOL_DIR_A}")
    def testset_a(self):
        """Test Set A (default). """
        ut_print("\nEnabling Test Set A")
        enable_testset_a()
        outputStr, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_A}",
                               check=False)
        self.assertEqual(outputStr, "",
                         msg=self.checkDiffMsg.format(diffOutput=outputStr))

    @unittest.skipIf(not os.path.exists(SOL_DIR_B), f"No dir: {SOL_DIR_B}")
    def testset_b(self):
        """Test Set B. """
        ut_print("\nEnabling Test Set B")
        enable_testset_b()
        outputStr, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_B}",
                               check=False)
        self.assertEqual(outputStr, "",
                         msg=self.checkDiffMsg.format(diffOutput=outputStr))

    @unittest.skipIf(not os.path.exists(SOL_DIR_C), f"No dir: {SOL_DIR_C}")
    def testset_c(self):
        """Test Set C. """
        ut_print("\nEnabling Test Set C")
        enable_testset_c()
        outputStr, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_C}",
                               check=False)
        self.assertEqual(outputStr, "",
                         msg=self.checkDiffMsg.format(diffOutput=outputStr))

    @unittest.skipIf(not os.path.exists(SOL_DIR_D), f"No dir: {SOL_DIR_D}")
    def testset_d(self):
        """Test Set D. """
        ut_print("\nEnabling Test Set D")
        enable_testset_d()
        outputStr, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_D}",
                               check=False)
        self.assertEqual(outputStr, "",
                         msg=self.checkDiffMsg.format(diffOutput=outputStr))


def mkdirs(dirStr):
    """Make directory if it does not exist. """
    if not os.path.exists(dirStr):
        os.makedirs(dirStr)


def trash_dir(dirStr):
    """Move a directory to trash/ ; rename if necessary. """
    if not os.path.exists(dirStr):
        return
    trashDir = "trash"
    toDir = f"{trashDir}/{dirStr}"
    while os.path.exists(toDir):
        reToDir = re.compile(r"([a-zA-Z\-]+)_(\d+)")
        searchToDir = reToDir.search(toDir)
        if searchToDir:
            idx = int(searchToDir.group(2))
            idx += 1
            toDir = f"{trashDir}/{searchToDir.group(1)}_{idx}"
        else:
            toDir = f"{trashDir}/{dirStr}_0"

    mkdirs(trashDir)
    print(f"Moving {dirStr} to {toDir}")
    shutil.move(dirStr, toDir)


def generate_solution_sets():
    """Generation solution test sets that are compared to with diff utility.
    """
    trash_dir(ARCHIVE_DIR)
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


if __name__ == '__main__':
    F_help = '-h' in sys.argv or '--help' in sys.argv
    F_generate = '-g' in sys.argv or '--generate' in sys.argv

    if F_help:
        scriptName = os.path.basename(__file__)
        print("------------------------------------------------------------")
        print(f"usage: {scriptName} [-g] [--generate] "
              f"to generate solution sets")
        print("---------------------------- or ----------------------------")

    if F_generate:
        generate_solution_sets()
    else:  # run tests as normal
        unittest.main()
