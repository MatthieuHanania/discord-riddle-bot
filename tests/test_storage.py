import unittest
import tempfile
import shutil
from pathlib import Path
from src.services.storage import StorageService


class TestStorageService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.storage = StorageService(guilds_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    async def test_new_guild_starts_empty(self):
        guild_id = 999999999
        data = await self.storage.get_guild_data(guild_id)
        self.assertEqual(data["riddle_text"], "")
        self.assertEqual(data["riddle_answer"], "")
        self.assertEqual(data["target_user_ids"], [])

    async def test_check_answer_when_empty(self):
        guild_id = 999999999
        is_correct, count, ans = await self.storage.check_answer(guild_id, 12345, "anything")
        self.assertFalse(is_correct)
        self.assertEqual(ans, "")

    async def test_set_riddle(self):
        guild_id = 999999999
        await self.storage.set_riddle(guild_id, "What has keys but no locks?", "piano")
        data = await self.storage.get_guild_data(guild_id)
        self.assertEqual(data["riddle_text"], "What has keys but no locks?")
        self.assertEqual(data["riddle_answer"], "piano")

        # Add target and check correct answer
        await self.storage.add_target(guild_id, 12345)
        is_correct, count, ans = await self.storage.check_answer(guild_id, 12345, "a piano")
        self.assertTrue(is_correct)
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
