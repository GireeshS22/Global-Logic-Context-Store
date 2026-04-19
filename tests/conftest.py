import pytest
from glcs.advanced_wrapper import AdvancedGLCS

@pytest.fixture(autouse=True, scope="session")
def setup_glcs():
    """Initialize GLCS before running tests."""
    from glcs.api.routes import initialize_glcs
    initialize_glcs(in_memory=True)

@pytest.fixture
def advanced_glcs():
    """Create AdvancedGLCS instance with in-memory storage for testing."""
    return AdvancedGLCS(
        parser_provider='ollama',
        encoder_model='all-mpnet-base-v2',
        in_memory=True,  # Use in-memory for faster tests
        collection_name='test_advanced',
    )