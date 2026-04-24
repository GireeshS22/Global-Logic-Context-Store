import pytest
from unittest.mock import MagicMock, patch
from glcs.cli import main
import sys

def test_cli_help(capsys):
    """Test that CLI help command works."""
    with patch.object(sys, 'argv', ['glcs', '--help']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0
    
    captured = capsys.readouterr()
    assert "GLCS - Global Logical Context Store CLI" in captured.out
    assert "process" in captured.out
    assert "verify" in captured.out

@patch('glcs.cli.AdvancedGLCS')
def test_cli_process_command(mock_glcs_class, capsys):
    """Test the 'process' CLI command."""
    mock_glcs = mock_glcs_class.return_value
    mock_report = MagicMock()
    mock_report.is_consistent = True
    mock_report.total_forms_checked = 1
    mock_glcs.process_statement.return_value = mock_report
    
    with patch.object(sys, 'argv', ['glcs', '--in-memory', 'process', 'Socrates is mortal', '--context', 'test-ctx']):
        code = main()
        assert code == 0
    
    mock_glcs.process_statement.assert_called_with('Socrates is mortal', 'test-ctx', auto_store=True)
    captured = capsys.readouterr()
    assert "✅ CONSISTENT" in captured.out

@patch('glcs.cli.AdvancedGLCS')
def test_cli_verify_command(mock_glcs_class, capsys):
    """Test the 'verify' CLI command."""
    mock_glcs = mock_glcs_class.return_value
    mock_report = MagicMock()
    mock_report.is_consistent = False
    mock_report.total_forms_checked = 5
    mock_violation = MagicMock()
    mock_violation.violation_type = "POLARITY_CONTRADICTION"
    mock_violation.explanation = "Test explanation"
    mock_violation.severity = "HIGH"
    mock_report.violations = [mock_violation]
    mock_glcs.verify_context.return_value = mock_report
    
    with patch.object(sys, 'argv', ['glcs', 'verify', '--context', 'test-ctx']):
        code = main()
        assert code == 1
    
    mock_glcs.verify_context.assert_called_with('test-ctx')
    captured = capsys.readouterr()
    assert "❌ INCONSISTENT" in captured.out
    assert "POLARITY_CONTRADICTION" in captured.out

@patch('glcs.cli.AdvancedGLCS')
def test_cli_list_contexts(mock_glcs_class, capsys):
    """Test the 'list-contexts' CLI command."""
    mock_glcs = mock_glcs_class.return_value
    mock_glcs.memory.list_contexts.return_value = ['ctx1', 'ctx2']
    mock_glcs.memory.get_context_stats.return_value = {'total_forms': 10}
    
    with patch.object(sys, 'argv', ['glcs', 'list-contexts']):
        code = main()
        assert code == 0
    
    captured = capsys.readouterr()
    assert "ctx1 (10 statements)" in captured.out
    assert "ctx2 (10 statements)" in captured.out

@patch('glcs.cli.AdvancedGLCS')
def test_cli_search_command(mock_glcs_class, capsys):
    """Test the 'search' CLI command."""
    mock_glcs = mock_glcs_class.return_value
    mock_res = MagicMock()
    mock_res.source_text = "Similar statement"
    mock_res.logical_type.value = "ground_fact"
    mock_res.confidence_score = 0.9
    mock_glcs.search_similar.return_value = [mock_res]
    
    with patch.object(sys, 'argv', ['glcs', 'search', 'query text', '--top-k', '3']):
        code = main()
        assert code == 0
    
    mock_glcs.search_similar.assert_called_with('query text', context_id=None, top_k=3)
    captured = capsys.readouterr()
    assert "Similar statement" in captured.out

@patch('glcs.cli.AdvancedGLCS')
def test_cli_clear_all_yes(mock_glcs_class, capsys):
    """Test the 'clear --all --yes' CLI command skips confirmation (#74)."""
    mock_glcs = mock_glcs_class.return_value
    mock_glcs.clear_all.return_value = 5
    
    # This should NOT call input() and should NOT hang
    with patch.object(sys, 'argv', ['glcs', 'clear', '--all', '--yes']):
        code = main()
        assert code == 0
    
    mock_glcs.clear_all.assert_called_once()
    captured = capsys.readouterr()
    assert "Cleared all 5 statements from storage." in captured.out
