#!/usr/bin/env python3
import os
import time
import numpy as np

times = []
N = 100
for i in range(N):
    startTime = time.time()
    os.system('optionset.py -q @op 2')
    thisTime = time.time() - startTime
    times.append(thisTime)
    print('Time [s]: {:1.5f}'.format(thisTime))

print('Avg time [s]: {:1.5f}'.format(np.mean(times)))
