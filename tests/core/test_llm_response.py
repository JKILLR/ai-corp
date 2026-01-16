"""
Tests for LLM Response Validation (FIX-010)

These tests verify that LLM responses are properly validated
and errors are handled correctly.
"""

import pytest

from src.core.llm import (
    validate_response,
    validate_json_fields,
    LLMResponse,
    LLMError
)


class TestLLMResponseFactoryMethods:
    """Test LLMResponse factory methods."""

    def test_success_response_creates_valid_response(self):
        """success_response should create a successful response."""
        response = LLMResponse.success_response(
            content="Hello world",
            parsed_json={"key": "value"}
        )
        assert response.success is True
        assert response.content == "Hello world"
        assert response.parsed_json == {"key": "value"}
        assert response.error is None

    def test_error_response_creates_error(self):
        """error_response should create a failed response."""
        response = LLMResponse.error_response(
            error="Something went wrong",
            content="partial content"
        )
        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.content == "partial content"


class TestValidateResponse:
    """Test the validate_response function."""

    def test_string_response_valid(self):
        """Simple string response should be valid."""
        response = validate_response("Hello world")
        assert response.success is True
        assert response.content == "Hello world"

    def test_dict_response_extracts_content(self):
        """Dict with 'content' field should be extracted."""
        response = validate_response({'content': 'Hello from API'})
        assert response.success is True
        assert response.content == 'Hello from API'

    def test_dict_response_extracts_text(self):
        """Dict with 'text' field should be extracted."""
        response = validate_response({'text': 'Hello from text'})
        assert response.success is True
        assert response.content == 'Hello from text'

    def test_dict_response_extracts_message(self):
        """Dict with 'message' field should be extracted."""
        response = validate_response({'message': 'Hello from message'})
        assert response.success is True
        assert response.content == 'Hello from message'

    def test_openai_format_response(self):
        """OpenAI-style response format should be handled."""
        response = validate_response({
            'choices': [{'message': {'content': 'OpenAI response'}}]
        })
        assert response.success is True
        assert response.content == 'OpenAI response'

    def test_none_response_returns_error(self):
        """None response should return error."""
        response = validate_response(None)
        assert response.success is False
        assert 'null' in response.error.lower()

    def test_empty_content_returns_error(self):
        """Empty content should return error."""
        response = validate_response({'content': '   '})
        assert response.success is False
        assert 'empty' in response.error.lower()

    def test_empty_string_returns_error(self):
        """Empty string should return error."""
        response = validate_response('')
        assert response.success is False
        assert 'empty' in response.error.lower()

    def test_whitespace_only_returns_error(self):
        """Whitespace-only string should return error."""
        response = validate_response('   \n\t   ')
        assert response.success is False
        assert 'empty' in response.error.lower()

    def test_json_parsing_when_expected(self):
        """JSON should be parsed when expect_json=True."""
        response = validate_response('{"key": "value"}', expect_json=True)
        assert response.success is True
        assert response.parsed_json == {'key': 'value'}

    def test_json_in_code_block_parsed(self):
        """JSON in markdown code block should be parsed."""
        content = '''```json
{"key": "value"}
```'''
        response = validate_response(content, expect_json=True)
        assert response.success is True
        assert response.parsed_json == {'key': 'value'}

    def test_json_in_code_block_no_language(self):
        """JSON in code block without language tag should be parsed."""
        content = '''```
{"key": "value"}
```'''
        response = validate_response(content, expect_json=True)
        assert response.success is True
        assert response.parsed_json == {'key': 'value'}

    def test_json_embedded_in_text(self):
        """JSON embedded in text should be extracted."""
        content = 'Here is the result: {"key": "value"} That was the output.'
        response = validate_response(content, expect_json=True)
        assert response.success is True
        assert response.parsed_json == {'key': 'value'}

    def test_json_array_parsed(self):
        """JSON array should be parsed."""
        response = validate_response('[1, 2, 3]', expect_json=True)
        assert response.success is True
        assert response.parsed_json == [1, 2, 3]

    def test_invalid_json_returns_error(self):
        """Invalid JSON should return error when expected."""
        response = validate_response('not valid json {', expect_json=True)
        assert response.success is False
        assert 'JSON' in response.error

    def test_invalid_json_preserves_content(self):
        """Invalid JSON should preserve original content in error response."""
        response = validate_response('not valid json {', expect_json=True)
        assert response.content == 'not valid json {'

    def test_no_json_parsing_by_default(self):
        """JSON should not be parsed by default."""
        response = validate_response('{"key": "value"}')
        assert response.success is True
        assert response.parsed_json is None
        assert response.content == '{"key": "value"}'

    def test_llm_response_passthrough(self):
        """Existing LLMResponse should pass through."""
        original = LLMResponse.success_response("test content")
        response = validate_response(original)
        assert response.success is True
        assert response.content == "test content"

    def test_failed_llm_response_passthrough(self):
        """Failed LLMResponse should pass through unchanged."""
        original = LLMResponse.error_response("original error")
        response = validate_response(original)
        assert response.success is False
        assert response.error == "original error"

    def test_raw_response_preserved(self):
        """Raw response should be preserved in result."""
        raw = {'content': 'test', 'metadata': 123}
        response = validate_response(raw)
        assert response.raw_response == raw


class TestValidateJsonFields:
    """Test the validate_json_fields function."""

    def test_valid_fields_pass(self):
        """Response with all required fields should pass."""
        response = LLMResponse.success_response(
            content='{"a": 1, "b": 2}',
            parsed_json={'a': 1, 'b': 2}
        )
        result = validate_json_fields(response, ['a', 'b'])
        assert result.success is True

    def test_missing_fields_fail(self):
        """Response missing required fields should fail."""
        response = LLMResponse.success_response(
            content='{"a": 1}',
            parsed_json={'a': 1}
        )
        result = validate_json_fields(response, ['a', 'b', 'c'])
        assert result.success is False
        assert 'b' in result.error
        assert 'c' in result.error

    def test_no_json_fails(self):
        """Response without parsed_json should fail."""
        response = LLMResponse.success_response(content='no json')
        result = validate_json_fields(response, ['a'])
        assert result.success is False
        assert 'no parsed JSON' in result.error

    def test_failed_response_passthrough(self):
        """Already failed response should pass through."""
        response = LLMResponse.error_response("original error")
        result = validate_json_fields(response, ['a', 'b'])
        assert result.success is False
        assert result.error == "original error"

    def test_empty_required_fields_passes(self):
        """Empty required fields list should always pass."""
        response = LLMResponse.success_response(
            content='{}',
            parsed_json={}
        )
        result = validate_json_fields(response, [])
        assert result.success is True


class TestLLMError:
    """Test LLMError exception."""

    def test_llm_error_is_exception(self):
        """LLMError should be an Exception."""
        assert issubclass(LLMError, Exception)

    def test_llm_error_message(self):
        """LLMError should store message."""
        error = LLMError("Something went wrong")
        assert str(error) == "Something went wrong"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_nested_json_in_code_block(self):
        """Nested JSON should be handled."""
        content = '''```json
{
    "outer": {
        "inner": {
            "value": 123
        }
    }
}
```'''
        response = validate_response(content, expect_json=True)
        assert response.success is True
        assert response.parsed_json['outer']['inner']['value'] == 123

    def test_json_with_special_characters(self):
        """JSON with special characters should be handled."""
        content = '{"message": "Hello\\nWorld\\t!", "emoji": "\\u2764"}'
        response = validate_response(content, expect_json=True)
        assert response.success is True
        assert 'Hello\nWorld\t!' in response.parsed_json['message']

    def test_multiple_json_objects_fails(self):
        """Multiple JSON objects in a row is invalid JSON."""
        content = '{"first": 1} {"second": 2}'
        response = validate_response(content, expect_json=True)
        # This is invalid JSON - parser finds braces but content between them is invalid
        assert response.success is False
        assert 'JSON' in response.error

    def test_dict_without_extractable_content(self):
        """Dict without any known content field should error."""
        response = validate_response({'data': 'value', 'info': 123})
        assert response.success is False
        assert 'extract content' in response.error.lower()

    def test_list_response_errors(self):
        """List response (not dict) should error."""
        response = validate_response(['a', 'b', 'c'])
        assert response.success is False

    def test_numeric_response_errors(self):
        """Numeric response should error."""
        response = validate_response(42)
        assert response.success is False
