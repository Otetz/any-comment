import pytest

from any_comment import create_app


@pytest.fixture
def app():
    application = create_app()
    return application
