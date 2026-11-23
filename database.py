
import copy
import json
import math
import os
import time


class ListValue:
    """Represent a database list separately from hash fields."""

    def __init__(self):
        self.items = []


class KeyValueDatabase:
    """Persistent key-value database with a custom list-based index."""

    def __init__(self, filename="data.db"):
        self.filename = filename
        self.records = []
        self.in_transaction = False
        self.transaction_snapshot = None
        self.pending_operations = []
        self.load()

    def find_index(self, key):
        """Find a key through linear search."""
        for index, record in enumerate(self.records):
            if record[0] == key:
                return index
        return -1

    def apply_set(self, key, value):
        """Set a value and reset its expiration."""
        index = self.find_index(key)
        record = [key, value, None]

        if index == -1:
            self.records.append(record)
        else:
            self.records[index] = record

    def apply_delete(self, key):
        """Remove a key from memory."""
        index = self.find_index(key)

        if index == -1:
            return 0

        self.records.pop(index)
        return 1

    def append_log(self, entry):
        """Durably append an operation to data.db."""
        with open(self.filename, "a", encoding="utf-8") as file:
            file.write(json.dumps(entry) + "\n")
            file.flush()
            os.fsync(file.fileno())

    def record_operation(self, entry):
        """Buffer transaction writes or persist normal writes."""
        if self.in_transaction:
            self.pending_operations.append(entry)
        else:
            self.append_log(entry)

    def set(self, key, value):
        """Store a key-value pair."""
        self.record_operation(["SET", key, value])
        self.apply_set(key, value)

    def get(self, key):
        """Get a value unless the key is missing or expired."""
        index = self.find_index(key)

        if index == -1:
            return None

        record = self.records[index]
        expires_at = record[2]

        if expires_at is not None and time.time() >= expires_at:
            return None

        return record[1]

    def exists(self, key):
        """Check whether an unexpired key exists."""
        return 1 if self.get(key) is not None else 0

    def delete(self, key):
        """Delete a key and record the operation."""
        if not self.exists(key):
            return 0

        self.record_operation(["DEL", key])
        return self.apply_delete(key)

    def mset(self, pairs):
        """Store multiple key-value pairs."""
        for key, value in pairs:
            self.set(key, value)

    def mget(self, keys):
        """Retrieve values in the requested order."""
        values = []

        for key in keys:
            values.append(self.get(key))

        return values

    def expire(self, key, seconds):
        """Assign an absolute expiration timestamp."""
        if not self.exists(key):
            return 0

        index = self.find_index(key)
        expires_at = time.time() + seconds

        self.record_operation(["EXPIRE", key, expires_at])
        self.records[index][2] = expires_at
        return 1

    def ttl(self, key):
        """Return the remaining time-to-live in seconds."""
        if not self.exists(key):
            return -2

        index = self.find_index(key)
        expires_at = self.records[index][2]

        if expires_at is None:
            return -1

        return max(0, math.ceil(expires_at - time.time()))

    def range_keys(self, start, end):
        """Return sorted keys within an inclusive range."""
        matching_keys = []

        for record in self.records:
            key = record[0]

            if not self.exists(key):
                continue

            if start != "" and key < start:
                continue

            if end != "" and key > end:
                continue

            matching_keys.append(key)

        matching_keys.sort()
        return matching_keys

    def apply_hset(self, key, field, value):
        """Update a hash field without writing to disk."""
        index = self.find_index(key)

        if index == -1:
            self.records.append([key, [[field, value]], None])
            return 1

        fields = self.records[index][1]

        if not isinstance(fields, list):
            return -1

        for item in fields:
            if item[0] == field:
                item[1] = value
                return 0

        fields.append([field, value])
        return 1

    def hset(self, key, field, value):
        """Persist a hash field and update the in-memory index."""
        index = self.find_index(key)

        if index != -1 and self.exists(key) == 0:
            self.apply_delete(key)
            index = -1

        if index != -1:
            if not isinstance(self.records[index][1], list):
                return -1

        self.record_operation(["HSET", key, field, value])
        return self.apply_hset(key, field, value)

    def hget(self, key, field):
        """Retrieve a single field from a hash."""
        fields = self.get(key)

        if not isinstance(fields, list):
            return None

        for item in fields:
            if item[0] == field:
                return item[1]

        return None

    def hgetall(self, key):
        """Return all fields and values from a hash."""
        fields = self.get(key)

        if not isinstance(fields, list):
            return []

        return [item.copy() for item in fields]


    def apply_push(self, key, value, left=False):
        """Add an item to a list in memory."""
        index = self.find_index(key)

        if index == -1:
            self.records.append([key, ListValue(), None])
            index = self.find_index(key)

        items = self.records[index][1]

        if not isinstance(items, ListValue):
            return -1

        if left:
            items.items.insert(0, value)
        else:
            items.items.append(value)

        return len(items.items)

    def lpush(self, key, value):
        """Prepend an item and persist the operation."""
        current = self.get(key)

        if current is not None and not isinstance(current, ListValue):
            return -1

        self.record_operation(["LPUSH", key, value])

        if current is None:
            self.apply_delete(key)

        return self.apply_push(key, value, left=True)

    def rpush(self, key, value):
        """Append an item and persist the operation."""
        current = self.get(key)

        if current is not None and not isinstance(current, ListValue):
            return -1

        self.record_operation(["RPUSH", key, value])

        if current is None:
            self.apply_delete(key)

        return self.apply_push(key, value)

    def lrange(self, key, start, stop):
        """Return list elements in the requested index range."""
        value = self.get(key)

        if not isinstance(value, ListValue):
            return []

        items = value.items
        length = len(items)

        if start < 0:
            start += length

        if stop < 0:
            stop += length

        start = max(0, start)
        stop = min(stop, length - 1)

        if start > stop:
            return []

        return items[start:stop + 1]

    def apply_lpop(self, key):
        """Remove the first list item from memory."""
        index = self.find_index(key)

        if index == -1:
            return None

        value = self.records[index][1]

        if not isinstance(value, ListValue) or not value.items:
            return None

        return value.items.pop(0)

    def lpop(self, key):
        """Remove, return, and persist the first list item."""
        value = self.get(key)

        if not isinstance(value, ListValue) or not value.items:
            return None

        self.record_operation(["LPOP", key])
        return self.apply_lpop(key)

    def change_counter(self, key, amount):
        """Increase or decrease a numeric key and persist the result."""
        current_value = self.get(key)

        # A nonexistent key starts at zero.
        if current_value is None:
            number = 0
        else:
            try:
                # Reject non-string values, such as hashes and lists.
                if not isinstance(current_value, str):
                    return None

                number = int(current_value)
            except ValueError:
                return None

        new_value = number + amount

        # Reuse SET for persistence and transaction support.
        self.set(key, str(new_value))

        return new_value

    def incr(self, key):
        """Increment a numeric key by one."""
        return self.change_counter(key, 1)

    def decr(self, key):
        """Decrement a numeric key by one."""
        return self.change_counter(key, -1)

    def flushdb(self):
        """Remove all keys and persist the database reset."""
        self.record_operation(["FLUSHDB"])
        self.records.clear()
        return True

    def begin(self):
        """Begin a transaction and save the current state."""
        if self.in_transaction:
            return False

        self.transaction_snapshot = copy.deepcopy(self.records)
        self.pending_operations = []
        self.in_transaction = True
        return True

    def commit(self):
        """Persist all transaction operations in one log record."""
        if not self.in_transaction:
            return False

        if self.pending_operations:
            self.append_log(["TXN", self.pending_operations])

        self.pending_operations = []
        self.transaction_snapshot = None
        self.in_transaction = False
        return True

    def abort(self):
        """Discard all uncommitted changes."""
        if not self.in_transaction:
            return False

        self.records = self.transaction_snapshot
        self.transaction_snapshot = None
        self.pending_operations = []
        self.in_transaction = False
        return True

    def apply_log_entry(self, entry):
        """Apply a persisted operation during recovery."""
        if not isinstance(entry, list) or not entry:
            return

        operation = entry[0]

        if operation == "SET" and len(entry) == 3:
            self.apply_set(entry[1], entry[2])

        elif operation == "DEL" and len(entry) == 2:
            self.apply_delete(entry[1])

        elif operation == "EXPIRE" and len(entry) == 3:
            index = self.find_index(entry[1])
            if index != -1:
                self.records[index][2] = entry[2]

        elif operation == "HSET" and len(entry) == 4:
            self.apply_hset(entry[1], entry[2], entry[3])

        elif operation == "LPUSH" and len(entry) == 3:
            self.apply_push(entry[1], entry[2], left=True)

        elif operation == "RPUSH" and len(entry) == 3:
            self.apply_push(entry[1], entry[2])

        elif operation == "LPOP" and len(entry) == 2:
            self.apply_lpop(entry[1])

        elif operation == "FLUSHDB" and len(entry) == 1:
            self.records.clear()

        elif operation == "TXN" and len(entry) == 2:
            if isinstance(entry[1], list):
                for pending_entry in entry[1]:
                    self.apply_log_entry(pending_entry)

    def load(self):
        """Replay the append-only log after restarting."""
        if not os.path.exists(self.filename):
            return

        with open(self.filename, "r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                except (ValueError, TypeError):
                    continue

                self.apply_log_entry(entry)
