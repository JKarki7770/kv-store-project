
import sys

from database import KeyValueDatabase


def main():
    """Run the key-value database command-line interface."""
    db = KeyValueDatabase()

    for line in sys.stdin:
        parts = line.strip().split(maxsplit=2)

        if not parts:
            continue

        command = parts[0].upper()

        if command == "EXIT":
            break

        elif command == "SET":
            if len(parts) != 3:
                print("ERROR")
                continue

            key = parts[1]
            value = parts[2]

            db.set(key, value)
            print("OK")

        elif command == "GET":
            if len(parts) != 2:
                print("ERROR")
                continue

            key = parts[1]
            value = db.get(key)

            if value is not None:
                print(value)
            else:
                print("")

        elif command == "EXISTS":
            if len(parts) != 2:
                print("ERROR")
                continue

            print(db.exists(parts[1]))

        elif command == "DEL":
            if len(parts) != 2:
                print("ERROR")
                continue

            print(db.delete(parts[1]))

        elif command == "MSET":
            arguments = line.strip().split()[1:]

            if len(arguments) < 2 or len(arguments) % 2 != 0:
                print("ERROR")
                continue

            pairs = []

            for i in range(0, len(arguments), 2):
                pairs.append([arguments[i], arguments[i + 1]])

            db.mset(pairs)
            print("OK")

        elif command == "MGET":
            keys = line.strip().split()[1:]

            if not keys:
                print("ERROR")
                continue

            values = db.mget(keys)

            for value in values:
                if value is None:
                    print("nil")
                else:
                    print(value)
        
        elif command == "EXPIRE":
            if len(parts) != 3:
                print("ERROR")
                continue

            key = parts[1]

            try:
                seconds = int(parts[2])
            except ValueError:
                print("ERROR")
                continue

            print(db.expire(key, seconds))

        elif command == "TTL":
            if len(parts) != 2:
                print("ERROR")
                continue

            print(db.ttl(parts[1]))

        elif command == "RANGE":
            if len(parts) != 3:
                print("ERROR")
                continue

            start = parts[1]
            end = parts[2]

            # Gradebot uses "" to represent an open boundary.
            if start == '""':
                start = ""

            if end == '""':
                end = ""

            keys = db.range_keys(start, end)

            for key in keys:
                print(key)

            print("END")

        elif command == "BEGIN":
            if len(parts) != 1:
                print("ERROR")
                continue

            if db.begin():
                print("OK")
            else:
                print("ERROR")

        elif command == "COMMIT":
            if len(parts) != 1:
                print("ERROR")
                continue

            if db.commit():
                print("OK")
            else:
                print("ERROR")

        elif command == "ABORT":
            if len(parts) != 1:
                print("ERROR")
                continue

            if db.abort():
                print("OK")
            else:
                print("ERROR")
        
        elif command == "HSET":
            if len(parts) != 3:
                print("ERROR")
                continue

            arguments = parts[2].split(maxsplit=1)

            if len(arguments) != 2:
                print("ERROR")
                continue

            key = parts[1]
            field = arguments[0]
            value = arguments[1]

            print(db.hset(key, field, value))

        elif command == "HGET":
            if len(parts) != 3:
                print("ERROR")
                continue

            key = parts[1]
            field = parts[2]

            value = db.hget(key, field)

            if value is None:
                print("nil")
            else:
                print(value)

        elif command == "HGETALL":
            if len(parts) != 2:
                print("ERROR")
                continue

            key = parts[1]
            fields = db.hgetall(key)

            for field, value in fields:
                print(field)
                print(value)
        
        elif command == "LPUSH":
            if len(parts) != 3:
                print("ERROR")
                continue

            key = parts[1]
            value = parts[2]

            print(db.lpush(key, value))

        elif command == "RPUSH":
            if len(parts) != 3:
                print("ERROR")
                continue

            key = parts[1]
            value = parts[2]

            print(db.rpush(key, value))

        elif command == "LRANGE":
            arguments = line.strip().split()

            if len(arguments) != 4:
                print("ERROR")
                continue

            key = arguments[1]

            try:
                start = int(arguments[2])
                stop = int(arguments[3])
            except ValueError:
                print("ERROR")
                continue

            items = db.lrange(key, start, stop)

            for item in items:
                print(item)

        elif command == "LPOP":
            if len(parts) != 2:
                print("ERROR")
                continue

            value = db.lpop(parts[1])

            if value is None:
                print("nil")
            else:
                print(value)

        elif command == "INCR":
            if len(parts) != 2:
                print("ERROR")
                continue

            result = db.incr(parts[1])

            if result is None:
                print("ERROR")
            else:
                print(result)

        elif command == "DECR":
            if len(parts) != 2:
                print("ERROR")
                continue

            result = db.decr(parts[1])

            if result is None:
                print("ERROR")
            else:
                print(result)

        elif command == "FLUSHDB":
            if len(parts) != 1:
                print("ERROR")
                continue

            db.flushdb()
            print("OK")

        else:
            print("ERROR")

        # Ensure output is immediately available to the tester.
        sys.stdout.flush()


if __name__ == "__main__":
    main()
