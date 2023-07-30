import pytest
from lib.csFactory import CSFactory

@pytest.fixture
def pat(request):
    return request.config.getoption('--pat')

def test_init(pat):
    # Use the obtained values as the arguments to initialize CSFactory
    argv = ["-p", pat, "-r", "https://github.com/ersilia-os/ersilia", "-s", "senti", "-o", "out"]

    cs_builder = CSFactory(argv)
        
    assert cs_builder is not None

def test_get_community_smells(pat):
    # Use the obtained values as the arguments to initialize CSFactory
    argv = ["-p", pat, "-r", "https://github.com/ersilia-os/ersilia", "-s", "senti", "-o", "out"]

    cs_builder = CSFactory(argv)

    result = cs_builder.getCommunitySmells()

    assert result is ""

