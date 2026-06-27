import re

BLOCKED_FLAGS = [
    "--script=malware", "--script=exploit", "--script=backdoor",
    "-oN", "-oX", "-oG", "-oA", "-oS",
    "--resume", "--append-output",
    "--datadir", "--servicedb", "--versiondb",
    "-iL", "-iR",
    "--script-args-file",
]

ALLOWED_PATTERN = re.compile(
    r'^(-p[\s\d,\-]+|'
    r'-T[0-5]|'
    r'--open|'
    r'-sV|-sC|-sS|-sT|-sU|-sN|-sF|-sX|'
    r'-O|'
    r'-A|'
    r'--script=[a-z0-9\-,]+|'
    r'--version-intensity\s+[0-9]|'
    r'--host-timeout\s+[\d]+[sm]|'
    r'--max-retries\s+[0-9]+|'
    r'--min-rate\s+[0-9]+|'
    r'--max-rate\s+[0-9]+)$'
)

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

    tokens = args.split()
    for token in tokens:
        if not ALLOWED_PATTERN.match(token):
            raise ValueError(f"Disallowed argument: '{token}'")

    return args
