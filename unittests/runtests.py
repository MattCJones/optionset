#!/usr/bin/env python3
"""
Run unit tests on optionset. See -h for help and -v for verbose
"""
import unittest
import os
import re
import subprocess
import shlex
import shutil
import sys
from time import time

RUNAPP = "../bin/optionset.py"  # run the application
LOG_FILE = ".log.optionset.py"
FILES_TO_TEST_DIR = "filesToTest"
ARCHIVE_DIR = "archive"
SOL_DIR_A = f"{ARCHIVE_DIR}/solSetA"
SOL_DIR_B = f"{ARCHIVE_DIR}/solSetB"
SOL_DIR_C = f"{ARCHIVE_DIR}/solSetC"
SOL_DIR_D = f"{ARCHIVE_DIR}/solSetD"


def ut_print(*args, **kwargs):
    """Print that takes into account verbosity level of test suite"""
    if ('-v' in sys.argv) or ('--verbose' in sys.argv):
        print(*args, **kwargs)


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


def enable_testset_a():
    """Enable Test Set A"""
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
            "~@$^&multipleTags a",
            "@nestedVarOp ' -12.34e-5'",
            "@variableOption ' -81.2e-2'",
            )
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUNAPP} {defOptionStr}")


def enable_testset_b():
    """Enable Test Set B"""
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
            "~@$^&multipleTags b",
            "@nestedVarOp 'eleventy two'",
            "@variableOption '112'",
            )
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUNAPP} {defOptionStr}")


def enable_testset_c():
    """Enable Test Set C"""
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
            "~@$^&multipleTags a",
            "@nestedVarOp ' -+ intermediate C 12.34e-5'",
            "@variableOption ' -+ 12.34e-5 C'",
            )
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUNAPP} {defOptionStr}")


def enable_testset_d():
    """Enable Test Set D"""
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
            "~@$^&multipleTags a",
            "@nestedVarOp ' -+ intermediate D 12.34e-5'",
            "@variableOption ' -+ 12.34e-5 D'",
            )
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUNAPP} {defOptionStr}")

    opSetStrs = (
            "@nestedL0 a",
            "@nestedL1 b",
            "@nestedL2 a",
            "@overlappingOption a",
            "@overlappingMultiline b",
            "@overlappingOptionShort none",
            "@nestedVarOp 'C -12.34E-5'",
            )
    for defOptionStr in opSetStrs:
        _, _ = run_cmd(f"{RUNAPP} {defOptionStr}")


def enable_default_options():
    """Set default options"""
    enable_testset_a()


@unittest.skipIf(False, "Skipping for debug")
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

        settingStr = "singleLine"
        outputStr, _ = run_cmd(f"{RUNAPP} {optionStr} {settingStr} -v")
        reMultiFileSingleLine = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reMultiFileSingleLine, outputStr))

        settingStr = "multiLine"
        outputStr, _ = run_cmd(f"{RUNAPP} {optionStr} {settingStr} -v")
        reMultiFileMultiLine = re.compile(f".*{optionStr} {settingStr}.*")
        self.assertTrue(test_regex(reMultiFileMultiLine, outputStr))

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


#@unittest.skip("Skipping for debug")
class TestSets(unittest.TestCase):
    """Run through Test Sets and verify output"""

    checkDiffMsg = "Differences in files shown below:\n{diffOutput}"

    def setUp(self):
        """Run before tests"""
        pass

    def tearDown(self):
        """Run after tests"""
        pass

    @classmethod
    def setUpClass(cls):
        ut_print("\nChecking all test sets")

    @classmethod
    def tearDownClass(cls):
        ut_print("\nResetting options")
        enable_default_options()

    @unittest.skipIf(not os.path.exists(SOL_DIR_A), f"No directory: {SOL_DIR_A}")
    def testset_a(self):
        """Test Set A (default)"""
        ut_print("\nEnabling Test Set A")
        enable_testset_a()
        outputStr, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_A}")
        self.assertEqual(outputStr, "", msg=self.checkDiffMsg.format(diffOutput=outputStr))

    @unittest.skipIf(not os.path.exists(SOL_DIR_B), f"No directory: {SOL_DIR_B}")
    def testset_b(self):
        """Test Set B"""
        ut_print("\nEnabling Test Set B")
        enable_testset_b()
        outputStr, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_B}")
        self.assertEqual(outputStr, "", msg=self.checkDiffMsg.format(diffOutput=outputStr))

    @unittest.skipIf(not os.path.exists(SOL_DIR_C), f"No directory: {SOL_DIR_C}")
    def testset_c(self):
        """Test Set C"""
        ut_print("\nEnabling Test Set C")
        enable_testset_c()
        outputStr, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_C}")
        self.assertEqual(outputStr, "", msg=self.checkDiffMsg.format(diffOutput=outputStr))

    @unittest.skipIf(not os.path.exists(SOL_DIR_D), f"No directory: {SOL_DIR_D}")
    def testset_d(self):
        """Test Set D"""
        ut_print("\nEnabling Test Set D")
        enable_testset_d()
        outputStr, _ = run_cmd(f"diff -r {FILES_TO_TEST_DIR} {SOL_DIR_D}")
        self.assertEqual(outputStr, "", msg=self.checkDiffMsg.format(diffOutput=outputStr))


def mkdirs(dirStr):
    """Make directory if it does not exist"""
    if not os.path.exists(dirStr):
        os.makedirs(dirStr)

def trash_dir(dirStr):
    """Move a directory to trash/ ; rename if necessary"""
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
    """Generation solution test sets that are compared to with diff utility"""
    trash_dir(ARCHIVE_DIR)
    #mkdirs(ARCHIVE_DIR)

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
        print(f"usage: {scriptName} [-g] [--generate] to generate solution sets")
        print("---------------------------- or ----------------------------")

    if F_generate:
        generate_solution_sets()
    else: # run tests as normal
        unittest.main()

