""" Utility-classes for optionset

Module for the Execution of optionset-commands and processing their output
"""


def version():
    """:return: Version number as a tuple"""
    return (2020, 1)


def versionString():
    """:return: Version number of PyFoam"""
    v = version()

    vStr = "%d" % v[0]
    for d in v[1:]:
        if type(d) == int:
            vStr += (".%d" % d)
        else:
            vStr += ("-%s" % str(d))
    return vStr

