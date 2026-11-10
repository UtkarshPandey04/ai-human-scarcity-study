"""Fast tests for agents/llm_client.py. No live API calls — everything network-shaped is mocked,
so `python tasks.py validate` stays free and runnable without any provider key configured. Live
verification against real Groq/Gemini keys is a manual step (see agents/llm_trial.py), not part of
this suite.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import agents.llm_client as llm_client
from agents.llm_client import (
    ChatMessage,
    LLMCompletionError,
    _complete_gemini,
    _messages_with_schema,
    _parse_json,
    _schema_instruction,
    clear_completion_cache,
    complete,
    ping_provider,
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
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_tel = llm_client.TELEMETRY_PATH
        llm_client.TELEMETRY_PATH = os.path.join(self._tmp.name, "api_telemetry.json")

    def tearDown(self):
        llm_client.TELEMETRY_PATH = self._orig_tel
        self._tmp.cleanup()

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

    def test_dispatches_to_ollama_backend(self):
        mock_ollama = MagicMock(return_value={"ok": True})
        with patch.dict("agents.llm_client.PROVIDERS", {"ollama": mock_ollama}):
            result = complete([ChatMessage(role="user", content="hi")], provider="ollama")
        self.assertEqual(result, {"ok": True})
        mock_ollama.assert_called_once()

    def test_missing_groq_key_raises_completion_error(self):
        clear_completion_cache()
        with patch.dict("os.environ", {}, clear=True):  # snapshot restored automatically on exit
            with self.assertRaises(LLMCompletionError):
                complete([ChatMessage(role="user", content="hi")], provider="groq")

    def test_key_getters_parse_comma_separated_pools(self):
        from agents.llm_client import get_gemini_api_keys, get_groq_api_keys, get_openrouter_api_keys
        with patch.dict("os.environ", {
            "GROQ_API_KEYS": "k1, k2, k3",
            "GEMINI_API_KEYS": "g1, g2",
            "OPENROUTER_API_KEYS": "o1, o2, o3",
        }):
            self.assertEqual(get_groq_api_keys(), ["k1", "k2", "k3"])
            self.assertEqual(get_gemini_api_keys(), ["g1", "g2"])
            self.assertEqual(get_openrouter_api_keys(), ["o1", "o2", "o3"])

    def test_fallback_chain_prioritizes_openrouter_over_gemini(self):
        from agents.llm_client import FALLBACK_CHAINS
        groq_chain = FALLBACK_CHAINS.get("groq", [])
        self.assertIn("openrouter", groq_chain)
        self.assertIn("gemini", groq_chain)
        self.assertLess(groq_chain.index("openrouter"), groq_chain.index("gemini"))

    def test_heterogeneous_dispatches_across_providers(self):
        mock_groq = MagicMock(return_value={"provider": "groq"})
        mock_openrouter = MagicMock(return_value={"provider": "openrouter"})
        clear_completion_cache()
        with patch.dict("agents.llm_client.PROVIDERS", {"groq": mock_groq, "openrouter": mock_openrouter}):
            with patch("agents.llm_client.get_available_providers", return_value=["groq", "openrouter"]):
                r1 = complete([ChatMessage(role="user", content="msg1")], provider="heterogeneous")
                r2 = complete([ChatMessage(role="user", content="msg2")], provider="heterogeneous")
        self.assertIn(r1.get("provider"), ("groq", "openrouter"))
        self.assertIn(r2.get("provider"), ("groq", "openrouter"))


class TestGeminiResilience(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_tel = llm_client.TELEMETRY_PATH
        llm_client.TELEMETRY_PATH = os.path.join(self._tmp.name, "api_telemetry.json")
        llm_client._BAD_API_KEYS.clear()
        llm_client._gemini_key_idx = 0

    def tearDown(self):
        llm_client._BAD_API_KEYS.clear()
        llm_client.TELEMETRY_PATH = self._orig_tel
        self._tmp.cleanup()

    def test_gemini_rotates_past_403_key_to_healthy_key(self):
        from google.genai import errors

        resp_ok = MagicMock()
        resp_ok.text = '{"action": "gather"}'
        resp_ok.usage_metadata = None

        def client_factory(api_key: str):
            mock_cli = MagicMock()
            if api_key == "bad_key_403":
                mock_cli.models.generate_content.side_effect = errors.APIError(
                    403, {"error": {"code": 403, "message": "free tier unavailable"}}, None
                )
            else:
                mock_cli.models.generate_content.return_value = resp_ok
            return mock_cli

        with patch.dict("os.environ", {"GEMINI_API_KEYS": "bad_key_403,good_key_1"}):
            with patch("google.genai.Client", side_effect=client_factory):
                usage = {}
                res = _complete_gemini([ChatMessage(role="user", content="hi")], None, None, 0.2, usage)

        self.assertEqual(res, {"action": "gather"})
        self.assertIn("bad_key_403", llm_client._BAD_API_KEYS)

    def test_gemini_fails_over_on_503_to_backup_flash_lite_model(self):
        from google.genai import errors

        resp_ok = MagicMock()
        resp_ok.text = '{"action": "share"}'
        resp_ok.usage_metadata = None
        seen_models = []

        def client_factory(api_key: str):
            mock_cli = MagicMock()

            def gen_content(model, contents, config):
                seen_models.append(model)
                if len(seen_models) == 1:
                    raise errors.APIError(503, {"error": {"code": 503, "message": "UNAVAILABLE"}}, None)
                return resp_ok

            mock_cli.models.generate_content.side_effect = gen_content
            return mock_cli

        with patch.dict("os.environ", {"GEMINI_API_KEYS": "g_key"}):
            with patch("google.genai.Client", side_effect=client_factory):
                usage = {}
                res = _complete_gemini([ChatMessage(role="user", content="hi")], None, None, 0.2, usage)

        self.assertEqual(res, {"action": "share"})
        self.assertEqual(len(seen_models), 2)
        self.assertNotEqual(seen_models[0], seen_models[1])

    def test_ping_provider_does_not_mask_error_with_fallback(self):
        mock_gemini_fail = MagicMock(side_effect=LLMCompletionError("gemini down"))
        mock_groq_ok = MagicMock(return_value={"ping": "pong"})
        with patch.dict("agents.llm_client.PROVIDERS", {"gemini": mock_gemini_fail, "groq": mock_groq_ok}):
            res = ping_provider("gemini")
        self.assertEqual(res["status"], "error")
        mock_groq_ok.assert_not_called()


if __name__ == "__main__":
    unittest.main()

