#!/usr/bin/env python
# Import and directly call optionset in a Python script
# This is equivalent to the 'myscript.sh' script

from optionset import optionset
optionset(['~nu', 'water'])  # set kinematic viscosity to that of water

optionset(['~nu', 'air', '--verbose'])  # reset to air
