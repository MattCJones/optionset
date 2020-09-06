#!/usr/bin/env python3
"""
Run unit tests on optionset.
"""
import unittest
import re
import subprocess
import shlex
import time

RUNAPP = "../bin/optionset.py"  # run the application
LOG_FILE = ".log.optionset.py"


def test_regex(regex, strToSearch):
    """Test that regex expression works for given strToSearch"""
    if regex.search(strToSearch):
        return True
    else:
        return False


def run_cmd(cmdStr):
    """Run a command and return the output"""
    subproc = subprocess.run(shlex.split(cmdStr), capture_output=True,
            check=True)
    outputStr = subproc.stdout.decode('UTF-8')
    return outputStr, subproc.returncode


def set_default_options():
    """Set default options"""
    defOptionStrs = ("@valid0Dir a", "@validExtension dat",
            "@validFileBaseDir a", "@validCommentType Bash",
            "@validFormat difficultPlacement", "@variableOption 1e-5",
            "@validSyntax difficultComments", "~@\$\^&multipleTags a",
            "@multiFile singleLine",
            "@overlappingOption a", "@overlappingOptionShort a",
            "@overlappingMultiline a",
            "@nestedL0 a", "@nestedL1 a", "@nestedL2 a",
            "@nestedVarOp ' -12.34e-5'",
            )
    for defOptionStr in defOptionStrs:
        _, _ = run_cmd(f"{RUNAPP} {defOptionStr}")


class TestIO(unittest.TestCase):
    """Test program through input and output"""

    def setUp(self):
        """Run before tests"""
        pass

    def tearDown(self):
        """Run after tests"""
        pass

    @classmethod
    def setUpClass(cls):
        print("Resetting options")
        set_default_options()

    @classmethod
    def tearDownClass(cls):
        print("\nResetting options")
        set_default_options()
    ############################################################
    # Test basic
    ############################################################
    def test_basic_io(self):
        """Test basic input and output"""
        reHasInputErr = re.compile(".*InputError.*")
        outputStr, _ = run_cmd(f"{RUNAPP}")
        self.assertTrue(test_regex(reHasInputErr, outputStr))

        reShowsUsage = re.compile("^usage:.*")
        outputStr, _ = run_cmd(f"{RUNAPP} -h")
        self.assertTrue(test_regex(reShowsUsage, outputStr))

    def test_ignored(self):
        """Test ignored files and directories"""
        reHasIgnoreStr = re.compile(".*shouldIgnore.*")
        outputStr, _ = run_cmd(f"{RUNAPP} -a")
        self.assertFalse(test_regex(reHasIgnoreStr, outputStr))

    def test_extensions(self):
        """Test various valid file extensions"""
        outputStr, _ = run_cmd(f"{RUNAPP} -a @validExtension")
        settingStrs = ('dat', 'nml', 'none', 'txt', 'org', 'orig', 'yaml',)
        for settingStr in settingStrs:
            reHasExtension = re.compile(f".*{settingStr}.*")
            self.assertTrue(test_regex(reHasExtension, outputStr))

    ############################################################
    # Test invalid format
    ############################################################
    def test_invalid(self):
        """Test invalid files and directories"""
        reInvalid = re.compile(".*ERROR.*")
        outputStr, _ = run_cmd(f"{RUNAPP} -a")
        self.assertFalse(test_regex(reInvalid, outputStr))

    ############################################################
    # Test valid format
    ############################################################
    def test_comment_types(self):
        """Test various comment types"""
        outputStr, _ = run_cmd(f"{RUNAPP} -a @validCommentType")
        settingStrs = ('Bash', 'CPP', 'MATLAB', 'NML', 'custom',)
        for settingStr in settingStrs:
            reCommentType = re.compile(f".*{settingStr}.*")
            self.assertTrue(test_regex(reCommentType, outputStr))

    def test_valid_syntax(self):
        """Test proper syntax of options and settings"""
        outputStr, _ = run_cmd(f"{RUNAPP} -a @validSyntax")
        settingStrs = ('difficultPlacement', 'multiline', 'difficultLine',
                'difficultComment',)
        for settingStr in settingStrs:
            reSyntax = re.compile(f".*{settingStr}.*")
            self.assertTrue(test_regex(reSyntax, outputStr))

    def test_variable_options(self):
        """Test variable option"""
        varSettingStr = '1e-8'
        reSetting = re.compile(f".*{varSettingStr}.*")

        outputStrBefore, _ = run_cmd(f"{RUNAPP} -a @variableOption")
        self.assertFalse(test_regex(reSetting, outputStrBefore))

        outputStrChange, _ = run_cmd(f"{RUNAPP} -v @variableOption {varSettingStr}")
        self.assertTrue(test_regex(reSetting, outputStrChange))

        outputStrAfter, _ = run_cmd(f"{RUNAPP} -a @variableOption")
        self.assertTrue(test_regex(reSetting, outputStrAfter))

    def test_multiple_tags(self):
        """Test multiple tags in options"""
        optionStr = r"~@$^&multipleTags"
        outputStr, _ = run_cmd(f"{RUNAPP} -a {optionStr}")
        reSyntax = re.compile(f".*\~\@\$\^\&multipleTags.*")
        self.assertTrue(test_regex(reSyntax, outputStr))

    def test_multiple_files(self):
        """Test options placed in multiple files"""
        optionStr = r"\@multiFile"

        settingStr = "multiLine"
        outputStr, _ = run_cmd(f"{RUNAPP} {optionStr} {settingStr} -v")
        reMultiFileMultiLine = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reMultiFileMultiLine, outputStr))

        settingStr = "singleLine"
        outputStr, _ = run_cmd(f"{RUNAPP} {optionStr} {settingStr} -v")
        reMultiFileSingleLine = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reMultiFileSingleLine, outputStr))

    def test_overlapping_options(self):
        """Test overlapping options"""
        optionStr = r"\@overlappingOption"
        settingStr = "c"
        outputStr, _ = run_cmd(f"{RUNAPP} {optionStr} {settingStr} -v")
        reOverlapping = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reOverlapping, outputStr))

        optionStr = r"\@overlappingOptionShort"
        settingStr = "c"
        outputStr, _ = run_cmd(f"{RUNAPP} {optionStr} {settingStr} -v")
        reOverlappingShort = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reOverlappingShort, outputStr))

    def test_nested_options(self):
        """Test multi-scoped options"""
        optionStr = r"\@nested"
        outputStr, _ = run_cmd(f"{RUNAPP} {optionStr} -a")

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
        outputStr, _ = run_cmd(f"{RUNAPP} {optionStr} {settingStr} -v")
        reNested = re.compile(f".*{settingStr}.*{optionStr}.*")
        self.assertTrue(test_regex(reNested, outputStr))


    ############################################################
    # Regression test: show that output is unchanged in with new version
    ############################################################
    def test_dotlog_output(self):
        f"""Test that {LOG_FILE} remains unchanged for basic input"""
        outputStr, _ = run_cmd(f"{RUNAPP} @none none")
        with open(LOG_FILE, 'r') as file:
            logStr = file.read()
        dotLogReStr = r"""INFO:root:Executing main function
INFO:root:Checking input options
INFO:root:<tag><option> <setting> = \\@none none
INFO:root:Generating valid files
INFO:root:Valid files: \[.*\]
INFO:root:Scrolling through files to set: \\@none none
WARNING:root:Skipping: ./filesToTest/shouldIgnore/tooLarge10kB.dat
WARNING:root:Reason: File exceeds kB size limit of 10
WARNING:root:Skipping: ./filesToTest/shouldIgnore/tooManyLines.dat
WARNING:root:Reason: File exceeds kB size limit of 10
INFO:root:Finished in \d+.\d+ s"""
        reRegressionMatch = re.compile(dotLogReStr)
        self.assertTrue(test_regex(reRegressionMatch, logStr))


if __name__ == '__main__':
    unittest.main()
