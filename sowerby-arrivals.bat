echo on
for %IDX in () do @(cls & python trainmon.py -a sow & timeout /t 30)