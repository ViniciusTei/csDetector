def pytest_addoption(parser):
    parser.addoption(
        '--pat', action='store', default='', help='GitHub access token to use the API'
    )
