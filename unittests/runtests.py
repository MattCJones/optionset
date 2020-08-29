#!/usr/bin/env python3
"""
Run unit tests on optionset.
"""
import unittest
import re
import subprocess
import shlex

RUNAPP = "../bin/optionset.py"  # run the application
LOG_FILE = ".log.optionset.py"


def test_re(regex, strToSearch):
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
            "@validFormat difficultPlacement", "@variableOption 1e-5")
    for defOptionStr in defOptionStrs:
        _, _ = run_cmd(f"{RUNAPP} {defOptionStr}")


class TestIO(unittest.TestCase):
    """Test input and output"""
    def setUp(self):
        pass

    def test_basic_io(self):
        """Test basic input and output"""
        reHasInputErr = re.compile(".*InputError.*")
        outputStr, _ = run_cmd(f"{RUNAPP}")
        self.assertTrue(test_re(reHasInputErr, outputStr))

        reShowsUsage = re.compile("^usage:.*")
        outputStr, _ = run_cmd(f"{RUNAPP} -h")
        self.assertTrue(test_re(reShowsUsage, outputStr))

    def test_ignored(self):
        """Test ignored files and directories"""
        reHasIgnoreStr = re.compile(".*shouldIgnore.*")
        outputStr, _ = run_cmd(f"{RUNAPP} -a")
        self.assertFalse(test_re(reHasIgnoreStr, outputStr))

    def test_extensions(self):
        """Test various valid file extensions"""
        outputStr, _ = run_cmd(f"{RUNAPP} -a @validExtension")
        settingStrs = ('dat', 'nml', 'none', 'txt', 'org', 'orig', 'yaml',)
        for settingStr in settingStrs:
            reHasExtension = re.compile(f".*{settingStr}.*")
            self.assertTrue(test_re(reHasExtension, outputStr))


class TestInvalid(unittest.TestCase):
    """Test invalid options"""
    def setUp(self):
        pass

    def test_invalid(self):
        """Test invalid files and directories"""
        reInvalid = re.compile(".*ERROR.*")
        outputStr, _ = run_cmd(f"{RUNAPP} -a")
        self.assertFalse(test_re(reInvalid, outputStr))

class TestValid(unittest.TestCase):
    """Test valid options"""
    def setUp(self):
        pass

    def test_comment_types(self):
        """Test various comment types"""
        outputStr, _ = run_cmd(f"{RUNAPP} -a @validCommentType")
        settingStrs = ('Bash', 'CPP', 'MATLAB', 'NML', 'custom',)
        for settingStr in settingStrs:
            reCommentType = re.compile(f".*{settingStr}.*")
            self.assertTrue(test_re(reCommentType, outputStr))

    def test_valid_syntax(self):
        """Test proper syntax of options and settings"""
        outputStr, _ = run_cmd(f"{RUNAPP} -a @validSyntax")
        settingStrs = ('difficultPlacement', 'multiline', 'difficultLine',
                'difficultComment',)
        for settingStr in settingStrs:
            reSyntax = re.compile(f".*{settingStr}.*")
            self.assertTrue(test_re(reSyntax, outputStr))

    def test_variable_options(self):
        """Test variable option"""
        varSettingStr = '1e-8'
        reSetting = re.compile(f".*{varSettingStr}.*")

        outputStrBefore, _ = run_cmd(f"{RUNAPP} -a @variableOption")
        self.assertFalse(test_re(reSetting, outputStrBefore))

        outputStrChange, _ = run_cmd(f"{RUNAPP} -v @variableOption {varSettingStr}")
        self.assertTrue(test_re(reSetting, outputStrChange))

        outputStrAfter, _ = run_cmd(f"{RUNAPP} -a @variableOption")
        self.assertTrue(test_re(reSetting, outputStrAfter))

    def test_multiple_indicator(self):
        """Test multiple indicators in options"""
        settingStr = r'~@$^&multiIndicator'
        outputStr, _ = run_cmd(f"{RUNAPP} -a {settingStr}")
        reSyntax = re.compile(r".*~@\$\^&multiIndicator.*")
        self.assertTrue(test_re(reSyntax, outputStr))


class TestRegression(unittest.TestCase):
    """Regression test: show that output is unchanged in with new version"""
    def setUp(self):
        pass

    def test_dotlog_output(self):
        f"""Test that {LOG_FILE} remains unchanged for basic input"""
        outputStr, _ = run_cmd(f"{RUNAPP} @none none")
        with open(LOG_FILE, 'r') as file:
            logStr = file.read()
        dotLogReStr = r"""INFO:root:Executing main function
INFO:root:Checking input options
INFO:root:<tag><option> <setting> = @none none
INFO:root:Generating valid files
INFO:root:Valid files: \[.*\]
INFO:root:Scrolling through files to set: @none none
WARNING:root:Skipping: ./filesToTest/shouldIgnore/tooLarge10kB.dat
WARNING:root:Reason: File exceeds kB size limit of 10
WARNING:root:Skipping: ./filesToTest/shouldIgnore/tooManyLines.dat
WARNING:root:Reason: File exceeds kB size limit of 10
INFO:root:Finished in \d+.\d+ s"""
        reRegressionMatch = re.compile(dotLogReStr)
        self.assertTrue(test_re(reRegressionMatch, logStr))


if __name__ == '__main__':
    set_default_options()
    unittest.main()
    set_default_options()
