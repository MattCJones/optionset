#!/usr/bin/env python3
import os
import time
import numpy as np

times = []
for i in range(100):
    startTime = time.time()
    os.system('optionset.py -q @op 2')
    thisTime = time.time() - startTime
    times.append(thisTime)
    print('Time [s]: {:1.5f}'.format(thisTime))

print('Avg time [s]: {:1.5f}'.format(np.mean(times)))
