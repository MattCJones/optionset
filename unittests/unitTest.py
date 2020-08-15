#!/usr/bin/env python3
import unittest
import re


# Regular expressions
ANY_WORD = '[a-zA-Z0-9._]+'
ANY_TAG = '[!@$^&*~]*'
ANY_NAME = r'\s+{}\s'.format(ANY_WORD)
ANY_GROUP = r'\s{}{}\s'.format(ANY_TAG, ANY_WORD)
ANY_COMMENT = r'(?:[#%]|//)'
uncommentedTagGroupName = re.compile('({}).*\s+({}{})\s+({})'.format(\
        ANY_COMMENT, ANY_TAG, ANY_WORD, ANY_WORD))
commentedTagGroupName = re.compile('^({0}).*{0}\s+({1}{2})\s+({3})'.format(\
        ANY_COMMENT, ANY_TAG, ANY_WORD, ANY_WORD))
findComment = re.compile('^\s*({})'.format(ANY_COMMENT))

def test_re(regex, sentence, group=0):
    """Test that regex expression works for given sentence """

    res = regex.search(sentence)
    if res:
        return res.group(group)
    else:
        return 'regex is None'
        
class TestStringMethods(unittest.TestCase):
    """Unit-test class """
    def setUp(self):
        self.comStrs = ['//', '#', '%']

    def test_comment_group_name_regex(self):
        for comStr in self.comStrs:
            commentedSentence = '{0}def(): {{x % 2.2}}[0 a],  &^$!@c.o_dE {0} @G_r0up  n_a.mE9'.format(comStr)
            unCommentedSentence = 'def(): {{x % 2.2}}[0 a],  &^$!@c.o_dE {0} @G_r0up  n_a.mE9'.format(comStr)
            # Find comment
            self.assertEqual(test_re(findComment, commentedSentence, group=0), comStr)
            # Check matching
            self.assertEqual(test_re(commentedTagGroupName,
                commentedSentence, group=1), comStr)
            self.assertEqual(test_re(commentedTagGroupName,
                commentedSentence, group=2), '@G_r0up')
            self.assertEqual(test_re(commentedTagGroupName,
                commentedSentence, group=3), 'n_a.mE9')
            # Should be false
            self.assertNotEqual(test_re(commentedTagGroupName,
                unCommentedSentence, group=1), comStr)
            self.assertNotEqual(test_re(commentedTagGroupName,
                unCommentedSentence, group=2), '@G_r0up')
            self.assertNotEqual(test_re(commentedTagGroupName,
                unCommentedSentence, group=3), 'n_a.mE9')

if __name__ == '__main__':
    unittest.main()
