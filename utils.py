def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

def transform_author(name: str):
    # authors are converted from the Last Name, First Name format
    if ',' not in name:
        return name
    return ' '.join(reversed(name.split(', ')))

def truncate_string(string, maxlen=80):
    """Truncates a string to "maxlen", adding ellipsis if necessary"""
    maxlen_ = maxlen - 3
    return (string[:maxlen_] + '...') if len(string) > maxlen else string
