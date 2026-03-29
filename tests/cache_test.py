#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import os
import orjson
from .base import JacazulTest


class FlowCacheTest(JacazulTest):
    """Tests for tw-flow output caching system."""

    def setUp(self):
        super().setUp()
        self.run_cmd(
            f"{self.tw_flow} ini cache_ini "
            "'Step 1|research|today' 'Step 2|implementation|tomorrow'"
        )
        out, _, _ = self.run_cmd(f"{self.taskp} project:cache_ini export")
        tasks = orjson.loads(out or "[]")
        self.u1 = tasks[0]["uuid"]
        self.u2 = tasks[1]["uuid"]
        self.cache_dir = os.path.join(
            self.test_dir, "cache", "tw-flow", "test_project", "global"
        )

    # ── Storage Layer ────────────────────────────────────────────────────────

    def test_cache_dir_created_on_first_status(self):
        """Cache: Running status must create the cache/ directory."""
        self.assertFalse(os.path.exists(self.cache_dir))
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.assertTrue(os.path.exists(self.cache_dir))

    def test_cache_file_created_for_ini_status(self):
        """Cache: Running status for an ini must create status_<ini>.json."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        cache_file = os.path.join(self.cache_dir, "status_cache_ini.json")
        self.assertTrue(os.path.exists(cache_file))

    def test_cache_file_structure_has_required_fields(self):
        """Cache: Cache file must contain hash, output, and ts fields."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        cache_file = os.path.join(self.cache_dir, "status_cache_ini.json")
        with open(cache_file, "rb") as f:
            data = orjson.loads(f.read())
        self.assertIn("hash", data)
        self.assertIn("output", data)
        self.assertIn("ts", data)

    def test_cache_dir_created_on_first_ponder(self):
        """Cache: Running ponder must create the cache/ directory."""
        self.assertFalse(os.path.exists(self.cache_dir))
        self.run_cmd(f"{self.tw_flow} ponder")
        self.assertTrue(os.path.exists(self.cache_dir))

    def test_cache_file_created_for_ponder(self):
        """Cache: Running ponder must create ponder.json cache file."""
        self.run_cmd(f"{self.tw_flow} ponder")
        cache_file = os.path.join(self.cache_dir, "ponder.json")
        self.assertTrue(os.path.exists(cache_file))

    # ── TTL / Prompt as Ad ───────────────────────────────────────────────────

    def test_status_cache_hit_within_ttl_shows_prompt_as_ad(self):
        """Cache: Second status within TTL must show Prompt as Ad, not full output."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.assertIn("[cached]", out)
        self.assertNotIn("══ Plan:", out)

    def test_ponder_cache_hit_within_ttl_shows_prompt_as_ad(self):
        """Cache: Second ponder within TTL must show Prompt as Ad, not full output."""
        self.run_cmd(f"{self.tw_flow} ponder")
        out, _, _ = self.run_cmd(f"{self.tw_flow} ponder")
        self.assertIn("[cached]", out)
        self.assertNotIn("[TASK LANDSCAPE]", out)

    # ── --force flag ─────────────────────────────────────────────────────────

    def test_status_force_bypasses_cache(self):
        """Cache: status --force must show full output even when cache is valid."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status cache_ini --force")
        self.assertNotIn("[cached]", out)
        self.assertIn("══ Plan:", out)

    def test_ponder_force_bypasses_cache(self):
        """Cache: ponder --force must show full output even when cache is valid."""
        self.run_cmd(f"{self.tw_flow} ponder")
        out, _, _ = self.run_cmd(f"{self.tw_flow} ponder --force")
        self.assertNotIn("[cached]", out)
        self.assertIn("[TASK LANDSCAPE]", out)

    # ── Cache Invalidation on Writes ─────────────────────────────────────────

    def test_cache_invalidated_on_note(self):
        """Cache Invalidation: Adding a note must bust status and ponder cache."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.run_cmd(f"{self.tw_flow} note {self.u1} decision 'Test decision'")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.assertNotIn("[cached]", out)
        self.assertIn("══ Plan:", out)

    def test_cache_invalidated_on_outcome(self):
        """Cache Invalidation: Recording an outcome must bust the cache."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Verified'")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.assertNotIn("[cached]", out)

    def test_cache_invalidated_on_done(self):
        """Cache Invalidation: Completing a task must bust the cache."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.run_cmd(f"{self.tw_flow} outcome {self.u1} 'Done'")
        self.run_cmd(f"{self.tw_flow} done {self.u1}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.assertNotIn("[cached]", out)
        self.assertIn("══ Plan:", out)

    def test_cache_invalidated_on_execute(self):
        """Cache Invalidation: Executing a task must bust the cache."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.run_cmd(f"{self.tw_flow} execute {self.u1}")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.assertNotIn("[cached]", out)

    def test_cache_invalidated_on_focus_change(self):
        """Cache Invalidation: Changing focus must bust status.json and ponder.json."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.run_cmd(f"{self.tw_flow} focus ini cache_ini")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.assertNotIn("[cached]", out)

    def test_other_ini_cache_unaffected_by_write_on_different_ini(self):
        """Cache Invalidation: Write on ini X must NOT bust cache for ini Y."""
        # Create a second ini
        self.run_cmd(f"{self.tw_flow} ini other_ini 'Other task|research|today'")
        out_exp, _, _ = self.run_cmd(f"{self.taskp} project:other_ini export")
        other_uuid = orjson.loads(out_exp)[0]["uuid"]

        # Prime cache for both
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.run_cmd(f"{self.tw_flow} status other_ini")

        # Write on cache_ini
        self.run_cmd(f"{self.tw_flow} note {self.u1} decision 'Bust cache_ini'")

        # other_ini cache should still be valid (Prompt as Ad)
        out, _, _ = self.run_cmd(f"{self.tw_flow} status other_ini")
        self.assertIn("[cached]", out)


class FlowCacheSubcommandTest(JacazulTest):
    """Tests for tw-flow cache subcommand (clear, info)."""

    def setUp(self):
        super().setUp()
        self.run_cmd(
            f"{self.tw_flow} ini cache_ini 'Step 1|research|today'"
        )
        self.cache_dir = os.path.join(
            self.test_dir, "cache", "tw-flow", "test_project", "global"
        )

    def _prime_cache(self):
        """Prime the cache by calling status and ponder."""
        self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.run_cmd(f"{self.tw_flow} ponder")

    # ── tw-flow cache info ───────────────────────────────────────────────────

    def test_cache_info_reports_zero_when_empty(self):
        """Cache info: Must report 0 files when cache is empty."""
        out, _, code = self.run_cmd(f"{self.tw_flow} cache info")
        self.assertEqual(code, 0)
        self.assertIn("0 file", out)

    def test_cache_info_reports_file_count_after_priming(self):
        """Cache info: Must report correct file count after priming."""
        self._prime_cache()
        out, _, code = self.run_cmd(f"{self.tw_flow} cache info")
        self.assertEqual(code, 0)
        self.assertNotIn("0 file", out)

    # ── tw-flow cache clear ──────────────────────────────────────────────────

    def test_cache_clear_all_removes_cache_dir(self):
        """Cache clear: Must remove all cache files."""
        self._prime_cache()
        self.assertTrue(os.path.exists(self.cache_dir))
        _, _, code = self.run_cmd(f"{self.tw_flow} cache clear")
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.cache_dir))

    def test_cache_clear_forces_fresh_status_output(self):
        """Cache clear: Status after clear must show full output, not cached."""
        self._prime_cache()
        # Confirm cached
        out, _, _ = self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.assertIn("[cached]", out)
        # Clear and verify fresh output
        self.run_cmd(f"{self.tw_flow} cache clear")
        out, _, _ = self.run_cmd(f"{self.tw_flow} status cache_ini")
        self.assertNotIn("[cached]", out)
        self.assertIn("══ Plan:", out)

    def test_cache_clear_status_scope_removes_only_status_files(self):
        """Cache clear status: Must remove status files, keep ponder."""
        self._prime_cache()
        ponder_file = os.path.join(self.cache_dir, "ponder.json")
        self.assertTrue(os.path.exists(ponder_file))
        self.run_cmd(f"{self.tw_flow} cache clear status")
        # ponder cache still exists
        self.assertTrue(os.path.exists(ponder_file))
        # status cache gone
        status_file = os.path.join(self.cache_dir, "status_cache_ini.json")
        self.assertFalse(os.path.exists(status_file))

    def test_cache_clear_ponder_scope_removes_only_ponder_files(self):
        """Cache clear ponder: Must remove ponder files, keep status."""
        self._prime_cache()
        status_file = os.path.join(self.cache_dir, "status_cache_ini.json")
        self.assertTrue(os.path.exists(status_file))
        self.run_cmd(f"{self.tw_flow} cache clear ponder")
        # status cache still exists
        self.assertTrue(os.path.exists(status_file))
        # ponder cache gone
        ponder_file = os.path.join(self.cache_dir, "ponder.json")
        self.assertFalse(os.path.exists(ponder_file))

    def test_session_isolation_different_sessions_have_separate_cache(self):
        """Cache: Two sessions must not share cache — session B gets fresh output."""
        session_a = "session_aaa"
        session_b = "session_bbb"
        # Session A primes cache
        self.run_cmd(
            f"{self.tw_flow} status cache_ini",
            env={"JACAZUL_SESSION_ID": session_a},
        )
        # Session B runs same command — must NOT get cached signal
        out, _, _ = self.run_cmd(
            f"{self.tw_flow} status cache_ini",
            env={"JACAZUL_SESSION_ID": session_b},
        )
        self.assertNotIn("[cached]", out)
        self.assertIn("══ Plan:", out)
