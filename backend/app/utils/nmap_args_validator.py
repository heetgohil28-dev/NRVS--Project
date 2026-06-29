import re

BLOCKED_FLAGS = [
    "--script=malware", "--script=exploit", "--script=backdoor",
    "-oN", "-oX", "-oG", "-oA", "-oS",
    "--resume", "--append-output",
    "--datadir", "--servicedb", "--versiondb",
    "-iL", "-iR",
    "--script-args-file",
]

MAX_ARGS_LENGTH = 200


def validate_custom_args(args: str) -> str:
    if not args or not args.strip():
        return ""

    args = args.strip()

    if len(args) > MAX_ARGS_LENGTH:
        raise ValueError(f"Custom args too long (max {MAX_ARGS_LENGTH} chars)")

    for blocked in BLOCKED_FLAGS:
        if blocked in args.lower():
            raise ValueError(f"Blocked flag detected: {blocked}")

    for char in [';', '&', '|', '`', '$', '>', '<', '\\', '\n', '\r']:
        if char in args:
            raise ValueError(f"Invalid character in custom args: '{char}'")

    # Validate each token
    ALLOWED_PATTERN = re.compile(
        r'^(-p[\d,\-]+$|'               # -p80,443 or -p1-1000
        r'-p$|'                          # -p alone (port list follows as next token)
        r'[\d,\-]+$|'                    # port list: 21,22,80 or 1-1000
        r'-T[0-5]$|'
        r'--open$|'
        r'-sV$|-sC$|-sS$|-sT$|-sU$|-sN$|-sF$|-sX$|'
        r'-O$|'
        r'-A$|'
        r'--script=[a-z0-9\-,]+$|'
        r'--version-intensity$|'
        r'--host-timeout$|'
        r'--max-retries$|'
        r'--min-rate$|'
        r'--max-rate$|'
        r'[0-9]+[sm]?$)'                 # numeric values for flags above
    )

    tokens = args.split()
    for token in tokens:
        if not ALLOWED_PATTERN.match(token):
            raise ValueError(f"Disallowed argument: '{token}'")

    return args
