
#!/usr/bin/env bash

# first argument is total number of cpus
# second argument is type of governor to set to.  Most likely to use
# 'ondemand' and 'performance'
for i in `seq 0 $(($1-1))`
do
    cpufreq-set --cpu $i  --governor $2
done