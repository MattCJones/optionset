#!/usr/bin/env python3
# This program enables and disables commented options. Use -h to view help.
#
# Author: Matthew Jones
# Email: weehikematt@yahoo.com
#
# To make this program executable anywhere, link it to the python directory
# found through the command "which python"

# TODO 2015-08-13: os.walk is slow for large amounts of files. any speedup?
# TODO 2015-09-25: make it so I can have overlapping options
# TODO 2016-01-14: have program check .data.cfg file for ignore dirs/files
# TODO 2016-01-14: have program do something intelligent if no arguments input
# TODO 2016-01-21: see potential bug in new snappyHexMeshDict with 'all' option
#       Multiline, multi option lines not working properly
# TODO 2016-01-21: explicitely turn a option off/on w/o effecting other options
# TODO 2016-02-18: get ^op to work
# TODO 2016-04-27: allow multiple input arguments? ./optionSet.py @op1 arg1 @op2 arg2
# TODO 2016-04-28: have shared options where @op2 is the dominant in // @op1 set1 @op2 set2
#   * The dominant option tells whether that line is commented or uncommented in -a
# TODO 2016-04-28: bug where ='' on inside of comment wraps next line on change

## Import files
import argparse
import logging
import os
import re
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from fnmatch import fnmatch
from functools import wraps
from pprint import pformat
from sys import exit
from time import time

## Time program
START_TIME = time()

## Set up input argument parser
DESCRIPTION= """
This program manipulates files in the base directory and below to comment and
un-comment specified lines of code.  In this way, code or in each file can be
'activated' or 'deactivated' conveniently.  Before running the program the user
must add special modifiers to the commented areas of each file to specify which 
lines of each file will be effected.  For example, the OpenFOAM dictionary text 
file 'system/controlDict' could be written as,

application pimpleFoam // @simulation transient
//application simpleFoam // @simulation steady

This setup allows the user to easily switch between transient and steady
simulations without manually editting the file.  Simply run,

{0} @simulation steady

and the dictionary file will be modified and re-written as,

//application pimpleFoam // @simulation transient
application simpleFoam // @simulation steady

where the steady solver 'simpleFoam' is now uncommented and active. Here
@simulation is the 'option' while transient and steady are the 'settings'.  
An unlimited number of unique options and settings are allowed.  Each can only
be composed of alphanumerical words with dots, pluses, minuses, and underscores.  
Note that the first one or more characters in a option must be a special symbol 
(non-bracket, non-comment-indicator, non-option/setting) such as '~`!@$%^&|\\?'.

Use '{0} -a ' to view all of the options that you have set, or even 
'{0} -a @simple' to view all options that begin with '@simple'.

To avoid comment clutter, multi-line options are encouraged by writing * in
front of the first and last options in a series (see text on left),

functions        // *@forces on    | <---  |   functions        // @forces on
{{                                  |INSTEAD|   {{                // @forces on
#include "forces"                  |  OF   |   #include "forces"// @forces on
}}                // *@forces on    | --->  |   }}                // @forces on
//               // @forces off    |       |   //               // @forces off

An additional feature is a variable option.  For variable options the dictionary
text file must be formatted with a Perl-styled regular expression ='<regex>' 
that matches the desired text to be changed such as,

variable option = 5.5; // @varOption ='= (.*);'

To change 'variable option' to 6.7 use, '{0} @varOption 6.7'. The file becomes,

variable option = 6.7; // @varOption ='= (.*);'

Using your favorite scripting language, it is convenient to glue this program 
into more advanced option variation routines.
""".format(__file__)
        
parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION)
parser.add_argument(
        'option', metavar='option', nargs='?', type=str, default=None,
        help='\'option\' name')
parser.add_argument(
        'setting', metavar='setting', nargs='?', type=str, default=None,
        help='\'setting\' for given \'option\'')
parser.add_argument(
        '-a', '--available', dest='available', default=False, action='store_true',
        help=('show available option-setting combinations. '
            'Allows for unix-style regular expression searching'))
parser.add_argument(
        '-v', '--verbose', dest='verbose', default=False, action='store_true',
        help='turn on verbose output')
parser.add_argument(
        '-q', '--quiet', dest='quiet', default=False, action='store_true',
        help='turn off all standard output')
parser.add_argument(
        '-d', '--debug', dest='debug', default=False, action='store_true',
        help='turn on debug output in log file')
args = parser.parse_args()

## Set up logging
BASENAME = os.path.basename(__file__)
LOG_PATH = '.log.{}'.format(BASENAME)
LOG_LEVEL = 'DEBUG' if args.debug else 'INFO'
if os.path.exists(LOG_PATH):
    os.remove(LOG_PATH)
logging.basicConfig(filename=LOG_PATH, level=LOG_LEVEL)

## Initialize global variables
IGNORE_DIRS = {'processor*', '.git', '[0-9]*.[0-9][^a-z]', 
        'triSurface', 'archive', '0', 'sets'}
IGNORE_FILES = {BASENAME, 'log.{}'.format(BASENAME), 'log.*', '*.py', 
        '*.gz', 'faces', 'neighbour', 'owner', 'points*', 'buildTestMatrix', 
        '*.stl', '*.png', '*.jpg'}
MAX_FLINES = 9999 # maximum lines per file
MAX_FSIZE_KB = 1000 # maximum file size, kilobytes

# Regular expression frameworks
ANY_COMMENT_IND = r'(?:[#%!]|//|--)' # comment indicators: # % // -- !
MULTI_TAG = r'[*]' # for multi-line commenting
ANY_WORD = r'[\+a-zA-Z0-9._-]+'
ANY_VAR = r'\={quote}.+{quote}'.format(quote=r'[\'"]')
ANY_SETTING = r'(?:{anyWord}|{anyVar})'.format(anyWord=ANY_WORD, anyVar=ANY_VAR)
ANY_INPUT_SETTING = '(?: |{})+'.format(ANY_WORD) # words with spaces (using '')
BRACKETS = r'[()<>\[\]]'
ANY_TAG = r'(?:(?!\s|{}|{}|{}|{}).)'.format(
        ANY_COMMENT_IND, MULTI_TAG, ANY_WORD, BRACKETS) # implicitely set
#ANY_TAG = r'[~`!@$^&\\\?\|]' # explicitely set
WHOLE_COMMENT = (r'(?P<comInd>{comInd})'
    r'(?P<wholeCom>.*\s+{mtag}*{tag}+{option}\s+{setting}\s.*\n?)')
UNCOMMENTED_LINE = r'(?P<nonCom>^\s*(?:(?!{comInd}).)+)' + WHOLE_COMMENT
COMMENTED_LINE = r'(?P<nonCom>^\s*{comInd}(?:(?!{comInd}).)+)' + WHOLE_COMMENT
ONLY_TAG_GROUP_SETTING = r'({mtag}*)({tag}+)({option})\s+({setting})\s'

# Error messages
INCOMPLETE_INPUT_MSG = '''InputError:
Incomplete input. Try:
    "{0} -h"                    to view help
    "{0} -a"                    to view available options
    "{0} -a <unix regex>"       to search options using a unix regex
    "{0} <option> <setting>"    to set the <setting> of <option>'''.format(__file__)
INVALID_OPTION_MSG = '''InputError:
Invalid option name. A preceding tag, such as '@' in '@option' is required, and
the rest of the option must adhere to the following regular expression: {0}
To view help try:
    "{1} -h"'''.format(ANY_WORD, __file__)
INVALID_SETTING_MSG = '''InputError:
Invalid setting name. The setting name must adhere to the following regular 
expression: {0}
To view help try:
    "{1} -h"'''.format(ANY_WORD, __file__)
INVALID_VAR_REGEX_MSG = '''FormatError:
Invalid 'variable setting' regular expression. The commented regular expression 
must adhere to this form: %(anyVar)s
(e.i. an equals sign followed by a user specified regular expression in quotes)
Additionally, the corresponding code on the line of this 'variable setting' must
match the user specified regular expression in quotes. This regular expression
must have one and only one set of parentheses surrounding the variable option to
be matched such as '(.*)'.  Otherwise, To specify literal parentheses in the 
regex, use '\('.
\r\nFile:{fileName}
Line {lineNum}:{line}
To view help try:
    "%(thisFile)s -h"''' % {'anyVar':ANY_VAR, 'thisFile':__file__}
PRINT_AVAIL_DEF_HDR_MSG = '''Printing available options and settings,
('  inactive  ', '> active <', '? both ?', '= variable ='):'''
INVALID_REGEX_GROUP_MSG = '''InvalidRegexGroupError: {specificProblem}.
A regular expression 'group' is denoted by a surrounding pair of parentheses '()'
The commented variable setting should be the only group.'
Use '()' to surround only the variable setting group in the commented regular expression.'''

## Define classes
class FileFlags:
    """Stores flags for line-by-line commenting features. """
    def __init__(self, F_fileModified=False, F_commented=None,
            F_multiLineActive=False, F_multiCommented=None):
        """Initialize flags. """
        self.F_fileModified = F_fileModified
        self.F_commented = F_commented
        self.F_multiLineActive = F_multiLineActive
        self.F_multiCommented = F_multiCommented
        
## Define utility functions
def print_available(db, globPat='*', headerMsg=PRINT_AVAIL_DEF_HDR_MSG):
    """Print available options and options for use; optionally sort with unix regex. """
    if headerMsg:
        print_and_log(headerMsg)
    logging.info(pformat(db, indent=1))
    for item in sorted(db.items()):
        if not fnmatch(item[0], globPat):
            continue
        print_and_log('  {}'.format(item[0]))
        for subItem in sorted(item[1].items()):
            if subItem[1] is True:
                leftStr, rightStr = '>', '<'
            elif subItem[1] is False:
                leftStr, rightStr = ' ', ' '
            elif subItem[1] is not None:
                leftStr, rightStr = subItem[1], subItem[1]
            else:
                leftStr, rightStr = '?', '?'
            print_and_log('\t{leftStr} {subItem[0]} {rightStr}'.format(**locals()))

def multi_line_logic(mtag, fFlags):
    """Set multi-line flags based on current conditions. """
    if mtag and not fFlags.F_multiLineActive:
        fFlags.F_multiLineActive = True
        fFlags.F_multiCommented = fFlags.F_commented
    elif mtag and fFlags.F_multiLineActive:
        fFlags.F_multiLineActive = False
        fFlags.F_multiCommented = None
    return fFlags

def log_before_after_commenting(func):
    """Wrapper to add file modifications to the log file. """
    @wraps(func)
    def log(*args_, **kwargs):
        lineBeforeMod = '[{:>4} ]{}'.format(args_[2], args_[0].rstrip('\r\n'))
        returnStr = func(*args_, **kwargs)
        lineAfterMod = '[{:>4}\']{}'.format(args_[2], returnStr.rstrip('\r\n'))
        if args.verbose:
            print_and_log(lineBeforeMod)
            print_and_log(lineAfterMod)
        else:
            logging.info(lineBeforeMod)
            logging.info(lineAfterMod)
        return returnStr
    return log

@log_before_after_commenting
def un_comment(line, comInd, lineNum):
    """Uncomment a line. Input requires comment indicator string. """
    line = re.sub(r'^\s*({})'.format(comInd), '', line)
    return line

@log_before_after_commenting
def comment(line, comInd, lineNum):
    """Comment a line. Input requires comment indicator string. """
    line = comInd + line
    return line

def check_number_groups(reStr):
    """Calculate the number of regex groups designated by (). """
    allGroups = re.findall(r'([^\\]\(.*?[^\\]\))', reStr)
    if allGroups is None:
        print_and_log(INVALID_REGEX_GROUP_MSG.format(
            specificProblem='No regex groups found.\r\n'))
        raise AttributeError
    elif len(allGroups) > 1:
        print_and_log(INVALID_REGEX_GROUP_MSG.format(
            specificProblem='More than one regex group \'()\' found'))
        raise AttributeError
    else:
        return(len(allGroups))

def add_left_right_groups(inLineRe):
    """Add left and right groups to regex.
    For example: \( (.*) 0 0 \) >>>> (\( )(.*)( 0 0 \)) """
    parensRe = (r'[^\\]([\(])', r'[^\\]([\)])')
    # Must add one to get rid of preceding character match
    leftParenInd = re.search(r'[^\\]([\(])', inLineRe).start() + 1
    rightParenInd = re.search(r'[^\\]([\)])', inLineRe).start() + 1
    left = inLineRe[:leftParenInd]
    mid = inLineRe[leftParenInd:rightParenInd + 1]
    right = inLineRe[rightParenInd + 1:]
    newInLineRe = '({left}){mid}({right})'.format(**locals())
    return newInLineRe

@log_before_after_commenting
def set_var_option(line, comInd, lineNum, replaceStr, inLineRe, strToReplace,
        nonCom, wholeCom):
    """Return line with new variable option set. """
    logging.info('Setting variable option:{}:{}'.format( inLineRe, replaceStr))
    # First ensure that there is only one () in the re
    #inLineReSearch = re.search(inLineRe, nonCom)
    # Next, add 2 new groups, one for the left side and the other for the right
    newInLineRe = add_left_right_groups(inLineRe)

    def replace_F(m):
        return m.group(1) + replaceStr + m.group(3)
    newNonCom = re.sub(newInLineRe, replace_F, nonCom)
    return newNonCom + comInd + wholeCom

def skip_file_warning(fileName, reason):
    """Log a warning that the current file is being skipped. """
    logging.warning('Skipping: {}'.format(fileName))
    logging.warning('Reason: {}'.format(reason))

def yield_utf8(file):
    """Yield file lines only if they are utf-8 encoded (non-binary). """
    try:
        for line in file:
            yield line
    except UnicodeDecodeError as err:
        skip_file_warning(file.name, err)

def line_count(fileName, lineLimit):
    """Return number of lines in a file unless file exceeds line limit. """
    lineCount = 0
    with open(fileName, 'r') as file:
        for line in yield_utf8(file):
            lineCount += 1
            if lineCount > lineLimit:
                return lineCount + 1 # return line limit +1 if line-count exheeds
    return lineCount

def get_comment_indicator(fileName):
    """Get comment indicator from fileName ('#', '//', or' %'). """
    with open(fileName, 'r') as file:
        comLineRe = re.compile(r'^\s*({}).*'.format(ANY_COMMENT_IND))
        for line in yield_utf8(file):
            searchComLine = comLineRe.search(line)
            if searchComLine:
                return searchComLine.group(1)

        logging.debug('Comment not found at start of line. Searching in-line.')
        formatVars = {'comInd':ANY_COMMENT_IND, 'mtag':MULTI_TAG, 'tag':ANY_TAG,
                'option':ANY_WORD, 'setting':ANY_SETTING}
        unComLineRe = re.compile(UNCOMMENTED_LINE.format(**formatVars))
        file.seek(0) # restart file
        for line in yield_utf8(file):
            searchUnComLine = unComLineRe.search(line)
            if searchUnComLine:
                return searchUnComLine.group('comInd')

def scroll_through_files(validFiles, F_getAvailable, inputOptions):
    """Scroll through files, line by line. This function:
    * Returns available options if F_getAvailable is enabled.
    * Sets given options if F_getAvailable is disabled. 
    * This is heart of the code. """
    allOptionsSettings = defaultdict(lambda: defaultdict(lambda: None))
    allVariableOptions = defaultdict(lambda: defaultdict(lambda: None))
    F_changesMade = False

    if F_getAvailable:
        logging.info('Scrolling through files to gather available options')
    else:
        logging.info(('Scrolling through files to set: '
            '{i.tag}{i.option} {i.setting}').format(i=inputOptions))

    for validFile in validFiles:
        logging.debug('FILE CANDIDATE: {}'.format(validFile))

        # Check file size and line count of file
        lineCount = line_count(validFile, lineLimit=MAX_FLINES)
        fsizeKb = os.stat(validFile).st_size/1000
        if fsizeKb > MAX_FSIZE_KB:
            skip_file_warning(validFile,
                    reason='File exceeds kB size limit of {}'.format(MAX_FSIZE_KB))
            continue
        elif lineCount > MAX_FLINES: 
            skip_file_warning(validFile,
                    reason='File exceeds line limit of {}'.format(MAX_FLINES))
            continue
        
        # Get string that signifies a commented line
        comInd = get_comment_indicator(validFile)
        if not comInd:
            continue
        logging.debug('FILE MATCHED [{}]: {}'.format(comInd, validFile))

        # Prepare regular expressions
        formatVars = {'comInd':comInd, 'mtag':MULTI_TAG, 'tag':inputOptions.tag,
                'option':inputOptions.option, 'setting':ANY_SETTING}
        comLineRe = re.compile(COMMENTED_LINE.format(**formatVars))
        unComLineRe = re.compile(UNCOMMENTED_LINE.format(**formatVars))
        tagOptionSettingRe = re.compile(ONLY_TAG_GROUP_SETTING.format(**formatVars))

        # Read file and parse options in comments
        with open(validFile, 'r') as file: 
            fFlags = FileFlags()
            newLines = ['']*lineCount
            for idx,line in enumerate(yield_utf8(file)):
                newLines[idx] = line
                lineNum = idx + 1
                searchCom = comLineRe.search(line)
                searchUnCom = unComLineRe.search(line)

                # Get whole commented part of line
                wholeCom, fFlags.F_commented = '', None
                if searchCom: # must search for commented before uncommented
                    nonCom, wholeCom = searchCom.group('nonCom', 'wholeCom')
                    fFlags.F_commented = True
                elif searchUnCom:
                    nonCom, wholeCom = searchUnCom.group('nonCom', 'wholeCom')
                    fFlags.F_commented = False
                elif fFlags.F_multiLineActive:
                    lineNum = idx+1
                    if fFlags.F_multiCommented:
                        newLine = un_comment(line, comInd, lineNum)
                    else:
                        newLine = comment(line, comInd, lineNum)
                    newLines[idx] = newLine # redundant
                    fFlags.F_fileModified = True
                else:
                    continue

                varErrMsg = INVALID_VAR_REGEX_MSG.format(fileName=validFile,
                        lineNum=lineNum, line=line)
                # Parse commented part of line
                for isearch in tagOptionSettingRe.finditer(wholeCom):
                    mtag,tag,option,setting = isearch.groups()
                    logging.debug(('\tMATCH com({fFlags.F_commented}) '
                        '[{idx}]:{comInd}:{tag}:{option}:{setting}').format(**locals()))
                    if F_getAvailable:
                        # Determine if option is enabled/disabled simultaneously
                        # TODO 2015-08-13: redundant code: fix
                        if re.search(ANY_VAR, setting) and not fFlags.F_commented: 
                            # Attribute handles regex fail. Index handles .group() fail
                            with handle_errors(errTypes=(AttributeError, IndexError), msg=varErrMsg):
                                #TODO 2015-08-16: handle sre_constants.error for unbalanced parentheses
                                inLineRe = setting[2:-1] # remove surrounding =''
                                check_number_groups(inLineRe)
                                strToReplace = re.search(inLineRe, nonCom).group(1)
                            allVariableOptions[tag+option][strToReplace] = '='
                        elif allOptionsSettings[tag+option][setting] is None:
                            allOptionsSettings[tag+option][setting] = (not fFlags.F_commented)
                        elif allOptionsSettings[tag+option][setting] != (not fFlags.F_commented):
                            allOptionsSettings[tag+option][setting] = '?'
                    else:
                        if re.search(ANY_VAR, setting) and not fFlags.F_commented:
                            with handle_errors(errTypes=AttributeError, msg=varErrMsg):
                                inLineRe = setting[2:-1] # remove surrounding =''
                                check_number_groups(inLineRe)
                                strToReplace = re.search(inLineRe, nonCom).group(1)
                            replaceStr = inputOptions.setting
                            if replaceStr == strToReplace:
                                logging.info('Option already set: {}'.format(replaceStr))
                            else:
                                with handle_errors(errTypes=AttributeError, msg=varErrMsg):
                                    newLines[idx] = set_var_option(line, comInd, lineNum,
                                            replaceStr, inLineRe, strToReplace, nonCom, wholeCom)
                                fFlags.F_fileModified = True
                        elif setting == inputOptions.setting and fFlags.F_commented:
                            newLines[idx] = un_comment(line, comInd, lineNum)
                            fFlags.F_fileModified = True
                            fFlags = multi_line_logic(mtag, fFlags)
                        elif setting != inputOptions.setting and not fFlags.F_commented:
                            newLines[idx] = comment(line, comInd, lineNum)
                            fFlags.F_fileModified = True
                            fFlags = multi_line_logic(mtag, fFlags)
                        else:
                            continue

        # Write file
        if fFlags.F_fileModified:
            with open(validFile, 'w') as file: 
                file.writelines(newLines)
            F_changesMade = True
            print_and_log('File modified: {}'.format(file.name))

    if F_getAvailable:
        # Cut out options with a singular setting. Could try filter() here
        cutOptionsSettings = { tg:n for tg,n in allOptionsSettings.items() if len(n) > 1}
        #cutVariableOptions = { tg:n for tg,n in allVariableOptions.items()}
        return cutOptionsSettings, allVariableOptions
    else:
        return F_changesMade

def fn_compare(globSet, compareArray):
    """Compare set with unix * expressions with array of files or directories. """
    for g in globSet:
        for c in compareArray:
            if fnmatch(c, g):
                return True
    else: # no break
        return False


def gen_valid_files():
    """Generator to get non-ignored files in non-ignored directories. """
    for dirPath, _, files in os.walk('.'):
        if not fn_compare(IGNORE_DIRS, dirPath.split(os.sep)):
            for file in files:
                if not fn_compare(IGNORE_FILES, (file,)):
                    yield '{}/{}'.format(dirPath, file)

def print_and_log(printStr):
    """Print to standard out and INFO level in log. """
    logging.info(printStr)
    if not args.quiet: 
        print(printStr)


@contextmanager
def handle_errors(errTypes, msg):
    """Use 'with:' to handle an error and print a message. """
    try:
        yield
    except errTypes as e:
        print_and_log(msg)
        exit()

def parse_and_check_input(args):
    """Parse input arguments. """
    InputOptions = namedtuple('InputOptions', ['tag', 'option', 'setting'])
    if args.available:
        return InputOptions(tag=ANY_TAG, option=ANY_WORD, setting=args.setting)
    else:
        # Check if both a option and a setting were input
        if args.setting is None or args.option is None:
            parser.print_usage()
            print_and_log(INCOMPLETE_INPUT_MSG)
            exit()
        # Check if setting is formatted correctly
        with handle_errors(errTypes=AttributeError, msg=INVALID_SETTING_MSG):
            setting = re.search(r'(^{}$)'.format(ANY_INPUT_SETTING), args.setting).group(0)
        # Check if option is formatted correctly
        checkTagOptionRe = re.compile(r'({}+)({})'.format(ANY_TAG, ANY_WORD))
        with handle_errors(errTypes=(AttributeError), msg=INVALID_OPTION_MSG):
            tag,option = checkTagOptionRe.search(args.option).groups()
        return InputOptions(tag=tag, option=option, setting=setting)

def main(args):
    """Main function. """
    logging.info('Executing main function')
    logging.info('Checking input options')
    inputOptions = parse_and_check_input(args)

    logging.info('<tag><option> <setting> = {} {}'.format(args.option, args.setting))
    logging.info('Generating valid files')
    validFiles = list(gen_valid_files()) # can run as generator
    logging.info('Valid files: {}'.format(validFiles))
    if args.available:
        tagsOptionsSettings, varOptions = scroll_through_files(validFiles,
                inputOptions=inputOptions, F_getAvailable=True)
        globPat = '*' if args.option is None else '{}*'.format(args.option)
        print_available(tagsOptionsSettings, globPat=globPat)
        if len(varOptions) > 0:
            print_available(varOptions, globPat=globPat, headerMsg=None)
    else:
        F_changesMade = scroll_through_files(validFiles, F_getAvailable=False,
                inputOptions=inputOptions)
        if F_changesMade:
            print_and_log('See all modifications in {}'.format(LOG_PATH))

    print_and_log('Finished in {:1.5f} s'.format(time() - START_TIME))

## Run main function
if __name__ == '__main__':
    main(args)
