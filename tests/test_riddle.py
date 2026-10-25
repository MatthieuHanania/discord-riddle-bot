"""Unit tests for RiddleBot riddle setup, storage, and UI view."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord

from src.services.storage import StorageService
from src.ui.riddle_views import RiddleView


class TestRiddleStorage(unittest.IsolatedAsyncioTestCase):
    """Tests for StorageService handling riddles, clues, and targets."""

    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = StorageService(guilds_dir=Path(self.temp_dir.name))

    async def asyncTearDown(self) -> None:
        self.temp_dir.cleanup()

    async def test_default_guild_data(self) -> None:
        guild_id = 12345
        data = await self.storage.get_guild_data(guild_id)
        self.assertEqual(data.get("definition"), "")
        self.assertEqual(data.get("indicators"), "")
        self.assertEqual(data.get("fodder"), "")
        self.assertNotIn("par", data)

    async def test_set_riddle_with_clues(self) -> None:
        guild_id = 99999
        await self.storage.set_riddle(
            guild_id=guild_id,
            text="12 - 55 + n = 9-12 (5)",
            answer="tween",
            definition="9-12",
            indicators="- (deletion) and + (addition)",
            fodder="'12', '55', and 'n'. (substitute)",
        )

        data = await self.storage.get_guild_data(guild_id)
        self.assertEqual(data["riddle_text"], "12 - 55 + n = 9-12 (5)")
        self.assertEqual(data["riddle_answer"], "tween")
        self.assertEqual(data["definition"], "9-12")
        self.assertEqual(data["indicators"], "- (deletion) and + (addition)")
        self.assertEqual(data["fodder"], "'12', '55', and 'n'. (substitute)")

    async def test_edit_riddle_partial_update(self) -> None:
        guild_id = 88888
        await self.storage.set_riddle(
            guild_id=guild_id,
            text="Initial Clue (5)",
            answer="apple",
            definition="A fruit",
            indicators="None",
            fodder="appl",
        )

        # Partially update only fodder
        await self.storage.edit_riddle(
            guild_id=guild_id,
            fodder="new fodder letters",
        )

        data = await self.storage.get_guild_data(guild_id)
        self.assertEqual(data["riddle_text"], "Initial Clue (5)")
        self.assertEqual(data["riddle_answer"], "apple")
        self.assertEqual(data["definition"], "A fruit")
        self.assertEqual(data["indicators"], "None")
        self.assertEqual(data["fodder"], "new fodder letters")

    async def test_set_last_riddle_message(self) -> None:
        guild_id = 77777
        await self.storage.set_last_riddle_message(guild_id, 1001, 2002)
        data = await self.storage.get_guild_data(guild_id)
        self.assertEqual(data["last_channel_id"], 1001)
        self.assertEqual(data["last_message_id"], 2002)

    async def test_check_answer_removes_target(self) -> None:
        guild_id = 11111
        user_id = 42
        await self.storage.clear_targets(guild_id)
        await self.storage.set_riddle(guild_id, "clue", "sol")
        await self.storage.add_target(guild_id, user_id)

        # Wrong answer
        is_correct, count, _ = await self.storage.check_answer(guild_id, user_id, "wrong")
        self.assertFalse(is_correct)
        self.assertEqual(count, 1)

        # Correct answer
        is_correct, count, _ = await self.storage.check_answer(guild_id, user_id, "sol")
        self.assertTrue(is_correct)
        self.assertEqual(count, 0)


class TestRiddleView(unittest.IsolatedAsyncioTestCase):
    """Tests for RiddleView buttons and interactive behavior."""

    def test_view_buttons_presence(self) -> None:
        mock_bot = MagicMock()
        view = RiddleView(mock_bot)

        custom_ids = [child.custom_id for child in view.children if hasattr(child, "custom_id")]
        self.assertIn("riddle:submit_answer_button", custom_ids)
        self.assertIn("riddle:rules_button", custom_ids)
        self.assertIn("riddle:definition_button", custom_ids)
        self.assertIn("riddle:indicators_button", custom_ids)
        self.assertIn("riddle:fodder_button", custom_ids)

        self.assertIsNone(view.timeout)

    def test_create_for_guild_dynamic_button_disabling(self) -> None:
        mock_bot = MagicMock()

        # Case 1: All clues present
        guild_data_full = {
            "definition": "Some definition",
            "indicators": "+ and -",
            "fodder": "letters",
        }
        view_full = RiddleView.create_for_guild(mock_bot, guild_data_full)
        self.assertFalse(view_full.definition_button.disabled)
        self.assertFalse(view_full.indicators_button.disabled)
        self.assertFalse(view_full.fodder_button.disabled)

        # Case 2: Only definition is set, indicators & fodder empty
        guild_data_partial = {
            "definition": "Only def",
            "indicators": "",
            "fodder": "   ",
        }
        view_partial = RiddleView.create_for_guild(mock_bot, guild_data_partial)
        self.assertFalse(view_partial.definition_button.disabled)
        self.assertTrue(view_partial.indicators_button.disabled)
        self.assertTrue(view_partial.fodder_button.disabled)

    async def test_clue_buttons_response(self) -> None:
        mock_bot = MagicMock()
        mock_bot.storage = AsyncMock()
        mock_bot.storage.get_guild_data.return_value = {
            "definition": "9-12",
            "indicators": "- and +",
            "fodder": "12, 55, n",
        }

        view = RiddleView(mock_bot)

        # Test definition button
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.guild_id = 12345
        interaction.response = AsyncMock()

        await view.definition_button.callback(interaction)
        interaction.response.send_message.assert_called_once()
        _, kwargs = interaction.response.send_message.call_args
        self.assertTrue(kwargs.get("ephemeral"))
        self.assertIn("9-12", kwargs["embed"].description)

        # Test indicators button
        interaction.response.reset_mock()
        await view.indicators_button.callback(interaction)
        interaction.response.send_message.assert_called_once()
        _, kwargs = interaction.response.send_message.call_args
        self.assertTrue(kwargs.get("ephemeral"))
        self.assertIn("- and +", kwargs["embed"].description)

        # Test fodder button
        interaction.response.reset_mock()
        await view.fodder_button.callback(interaction)
        interaction.response.send_message.assert_called_once()
        _, kwargs = interaction.response.send_message.call_args
        self.assertTrue(kwargs.get("ephemeral"))
        self.assertIn("12, 55, n", kwargs["embed"].description)


if __name__ == "__main__":
    unittest.main()
