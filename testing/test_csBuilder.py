import pytest
from lib.csBuilder import CSBuilder

def test_init():
    # Simulate passing command-line arguments (empty list for simplicity)
    argv = []
    
    # Ensure the __init__ method doesn't raise any exceptions
    with pytest.raises(Exception) as e_info:
        cs_builder = CSBuilder(argv)
        
    assert e_info.value is None

