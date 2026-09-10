"""Fast tests for agents/llm_client.py. No live API calls — everything network-shaped is mocked,
so `python tasks.py validate` stays free and runnable without any provider key configured. Live
verification against real Groq/Gemini keys is a manual step (see agents/llm_trial.py), not part of
this suite.
"""

import unittest
from unittest.mock import MagicMock, patch

from agents.llm_client import (
    ChatMessage,
    LLMCompletionError,
    _messages_with_schema,
    _parse_json,
    _schema_instruction,
    complete,
)


class TestSchemaInstruction(unittest.TestCase):
    def test_none_schema_gives_none_instruction(self):
        self.assertIsNone(_schema_instruction(None))

    def test_schema_renders_as_json_in_instruction(self):
        instruction = _schema_instruction({"type": "object"})
        self.assertIn('"type": "object"', instruction)


class TestMessagesWithSchema(unittest.TestCase):
    def test_no_schema_leaves_messages_unchanged(self):
        messages = [ChatMessage(role="user", content="hi")]
        self.assertEqual(_messages_with_schema(messages, None), messages)

    def test_schema_appends_to_last_message_only(self):
        messages = [ChatMessage(role="system", content="sys"), ChatMessage(role="user", content="hi")]
        result = _messages_with_schema(messages, {"type": "object"})
        self.assertEqual(result[0].content, "sys")  # untouched
        self.assertIn("hi", result[1].content)
        self.assertIn('"type": "object"', result[1].content)


class TestParseJson(unittest.TestCase):
    def test_valid_json_parses(self):
        self.assertEqual(_parse_json('{"a": 1}', "test"), {"a": 1})

    def test_invalid_json_raises_llm_completion_error(self):
        with self.assertRaises(LLMCompletionError):
            _parse_json("not json", "test")


class TestCompleteDispatch(unittest.TestCase):
    def test_unknown_provider_raises_value_error(self):
        with self.assertRaises(ValueError):
            complete([ChatMessage(role="user", content="hi")], provider="not_a_real_provider")

    def test_dispatches_to_groq_backend(self):
        # PROVIDERS binds function references at import time, so patching the standalone name
        # `agents.llm_client._complete_groq` does NOT change what the dict calls — caught live:
        # doing exactly that here originally made a real, uncontrolled call to the Groq API
        # during a supposedly no-network test run. Patch the dict entry itself instead.
        mock_groq = MagicMock(return_value={"ok": True})
        with patch.dict("agents.llm_client.PROVIDERS", {"groq": mock_groq}):
            result = complete([ChatMessage(role="user", content="hi")], provider="groq")
        self.assertEqual(result, {"ok": True})
        mock_groq.assert_called_once()

    def test_dispatches_to_gemini_backend(self):
        mock_gemini = MagicMock(return_value={"ok": True})
        with patch.dict("agents.llm_client.PROVIDERS", {"gemini": mock_gemini}):
            result = complete([ChatMessage(role="user", content="hi")], provider="gemini")
        self.assertEqual(result, {"ok": True})
        mock_gemini.assert_called_once()

    def test_missing_groq_key_raises_completion_error(self):
        with patch.dict("os.environ", {}, clear=True):  # snapshot restored automatically on exit
            with self.assertRaises(LLMCompletionError):
                complete([ChatMessage(role="user", content="hi")], provider="groq")


if __name__ == "__main__":
    unittest.main()
