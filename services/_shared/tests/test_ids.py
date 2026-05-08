import pytest
from yp_shared.ids import generate_id, parse_id

def test_generate_and_parse_id():
    new_id = generate_id("dev")
    assert new_id.startswith("dev_")
    
    parsed = parse_id(new_id)
    assert len(parsed) == 26  # ULID length
    
def test_parse_invalid_id():
    with pytest.raises(ValueError):
        parse_id("invalid-format")
