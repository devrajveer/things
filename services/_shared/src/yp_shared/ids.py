import ulid

def generate_id(prefix: str) -> str:
    """Generate a ULID with a given prefix."""
    return f"{prefix}_{ulid.new().str}"

def parse_id(prefixed_id: str) -> str:
    """Parse and validate a prefixed ULID, returning the raw ULID string."""
    try:
        prefix, ulid_str = prefixed_id.split("_", 1)
        # Validate that it's a correct ULID by parsing
        parsed = ulid.parse(ulid_str)
        return parsed.str
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid prefixed ID format: {prefixed_id}") from e
