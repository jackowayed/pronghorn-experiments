import csv

def find_window(times, warmup=0.0):
    """Finds the window of data we want to use.
    We only want times when all threads were running.
    Returns (start, end)
    Cuts out the first warmup proportion of the time"""
    last_start = max([ t[0] for t in times])
    first_end = min([ t[-1] for t in times])

    # do warmup
    end = first_end
    warmup_time = (end - last_start) * warmup
    start = last_start + warmup_time
    return (start, end)


def find_throughput(times, warmup=0.0):
    start, end = find_window(times, warmup)

    # TODO inefficient because we know things are sorted. should use bisect
    trimmed = [ [ t for t in arr if t >= start and t <= end ] for arr in times ]

    num_ops = sum([ len(t) for t in trimmed])
    elapsed = end - start #nanoseconds
    #print "ops:", num_ops, "elapsed:", elapsed, "start:", start, "end:", end
    throughput = (num_ops * 1000000000) / elapsed
    return throughput

def read_times(fname):
    times = []
    with open(fname, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            times.append([ int(t) for t in row ])
    return times


def throughput(csv_fname, warmup=0.0):
    times = read_times(csv_fname)
    return find_throughput(times, warmup)

