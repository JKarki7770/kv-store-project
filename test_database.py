
import os
import tempfile
import unittest

from database import KeyValueDatabase


class TestKeyValueDatabase(unittest.TestCase):
    """Automated tests for the persistent key-value database."""

    def setUp(self):
        """Create an isolated database for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "data.db")
        self.db = KeyValueDatabase(self.db_path)

    def tearDown(self):
        """Remove temporary files after each test."""
        self.temp_dir.cleanup()

    def test_set_get(self):
        self.db.set("name", "Janak")
        self.assertEqual(self.db.get("name"), "Janak")

    def test_overwrite(self):
        self.db.set("name", "Janak")
        self.db.set("name", "John")
        self.assertEqual(self.db.get("name"), "John")

    def test_nonexistent_key(self):
        self.assertIsNone(self.db.get("missing"))

    def test_persistence(self):
        self.db.set("university", "UNT")

        restarted_db = KeyValueDatabase(self.db_path)

        self.assertEqual(restarted_db.get("university"), "UNT")

    def test_delete_exists(self):
        self.db.set("city", "Denton")

        self.assertEqual(self.db.exists("city"), 1)
        self.assertEqual(self.db.delete("city"), 1)
        self.assertEqual(self.db.exists("city"), 0)

    def test_mset_mget(self):
        self.db.mset([
            ["a", "apple"],
            ["b", "banana"]
        ])

        self.assertEqual(
            self.db.mget(["a", "b", "missing"]),
            ["apple", "banana", None]
        )

    def test_expiration(self):
        self.db.set("temporary", "hello")
        self.assertEqual(self.db.expire("temporary", 0), 1)

        self.assertIsNone(self.db.get("temporary"))
        self.assertEqual(self.db.ttl("temporary"), -2)

    def test_range(self):
        self.db.mset([
            ["a", "1"],
            ["b", "2"],
            ["c", "3"],
            ["d", "4"]
        ])

        self.assertEqual(
            self.db.range_keys("b", "c"),
            ["b", "c"]
        )

    def test_transaction_abort(self):
        self.db.begin()
        self.db.set("course", "CSCE4350")
        self.db.abort()

        self.assertIsNone(self.db.get("course"))

    def test_transaction_commit(self):
        self.db.begin()
        self.db.set("course", "CSCE4350")
        self.db.commit()

        restarted_db = KeyValueDatabase(self.db_path)

        self.assertEqual(restarted_db.get("course"), "CSCE4350")

    def test_hash_commands(self):
        self.db.hset("student", "name", "Janak")
        self.db.hset("student", "university", "UNT")

        self.assertEqual(self.db.hget("student", "name"), "Janak")
        self.assertEqual(
            self.db.hgetall("student"),
            [["name", "Janak"], ["university", "UNT"]]
        )

    def test_list_commands(self):
        self.db.lpush("fruits", "apple")
        self.db.rpush("fruits", "banana")
        self.db.lpush("fruits", "orange")

        self.assertEqual(
            self.db.lrange("fruits", 0, -1),
            ["orange", "apple", "banana"]
        )

        self.assertEqual(self.db.lpop("fruits"), "orange")

    def test_counter(self):
        self.assertEqual(self.db.incr("counter"), 1)
        self.assertEqual(self.db.incr("counter"), 2)
        self.assertEqual(self.db.decr("counter"), 1)

    def test_flushdb(self):
        self.db.set("a", "1")
        self.db.set("b", "2")

        self.db.flushdb()

        self.assertIsNone(self.db.get("a"))
        self.assertIsNone(self.db.get("b"))

        restarted_db = KeyValueDatabase(self.db_path)

        self.assertIsNone(restarted_db.get("a"))


if __name__ == "__main__":
    unittest.main()
