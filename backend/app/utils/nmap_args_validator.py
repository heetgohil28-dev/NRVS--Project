import re

# Blocked dangerous flags
BLOCKED_FLAGS = [
    "--script=malware", "--script=exploit", "--script=backdoor",
    "-oN", "-oX", "-oG", "-oA", "-oS",  # output to file
    "--resume", "--append-output",
    "--datadir", "--servicedb", "--versiondb",
    "-iL", "-iR",  # input from file
    "--script-args-file",
]

# Only allow safe flag patterns
ALLOWED_PATTERN = re.compile(
    r'^(-p[\s\d,\-]+|'           # ports: -p 80,443
    r'-T[0-5]|'                   # timing: -T3
    r'--open|'                    # --open
    r'-sV|-sC|-sS|-sT|-sU|-sN|-sF|-sX|'  # scan types
    r'-O|'                        # OS detection
    r'-A|'                        # aggressive
    r'--script=[a-z0-9\-,]+|'    # safe scripts only
    r'--version-intensity\s+[0-9]|'
    r'--host-timeout\s+[\d]+[sm]|'
    r'--max-retries\s+[0-9]+|'
    r'--min-rate\s+[0-9]+|'
    r'--max-rate\s+[0-9]+)'
)

MAX_ARGS_LENGTH = 200


def validate_custom_args(args: str) -> str:
    """
    Validate and sanitize custom nmap arguments.
    Raises ValueError if dangerous flags are detected.
    """
    if not args or not args.strip():
        return ""

    args = args.strip()

    if len(args) > MAX_ARGS_LENGTH:
        raise ValueError(f"Custom args too long (max {MAX_ARGS_LENGTH} chars)")

    # Check for blocked flags
    for blocked in BLOCKED_FLAGS:
        if blocked in args.lower():
            raise ValueError(f"Blocked flag detected: {blocked}")

    # Check for shell injection
    for char in [';', '&', '|', '`', '$', '>', '<', '\\', '\n', '\r']:
        if char in args:
            raise ValueError(f"Invalid character in custom args: '{char}'")

    return args
