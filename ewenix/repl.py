from ewenix.util import now, mint
from ewenix.monad import Nil
from ewenix.scheduler import Scheduler
from ewenix.algorithms import Memory
from ewenix.encoding import bencode, bdecode

class REPL:
    def __init__(self):
        self.sched = Scheduler()
        self.mem = Memory(32*1024)

    def encode(self, data, enc=False):
        return bencode(data, enc=enc)

    def decode(self, data):
        return bdecode(data)

    def read(self):
        return input("ewenix> ")

    def eval(self, data):
        commands = dict()
        commands["help"] = "Display this message"
        commands["print"] = "Print back input"
        commands["echo"] = "Print back input with a delay"
        commands["alloc"] = "Allocate blocks of memory"
        commands["free"] = "Free blocks of memory"
        commands["write"] = "Write to blocks of memory"
        commands["read"] = "Read from blocks of memory"
        commands["bwrite"] = "Write bencode to blocks of memory"
        commands["bread"] = "Read bencode from blocks of memory"
        commands["quit"] = "Exit the REPL"

        parts = list()
        cache = ""
        mode = 0
        for i in range(len(data)):
            char = data[i]
            if char == "@":
                mode = 3
                continue

            if char == "\"":
                if mode == 0:
                    mode = 2
                    continue

                elif mode == 1:
                    parts.append(cache)
                    cache = ""
                    mode = 0
                    continue

            elif char == " " and mode not in [1,3]:
                parts.append(cache)
                cache = ""
                mode = 0
                continue

            cache = cache + char
            continue

        parts.append(cache)

        if parts[0] == "help":
            dialog = "\n".join(f"{k} - {v}" for k, v in commands.items())
            return True, dialog

        elif parts[0] == "print":
            return True, " ".join(parts[1:])

        elif parts[0] == "echo":
            suspend = now() + mint(parts[1], 0)
            content = " ".join(parts[2:])
            jobid = self.sched.push(f"print {content}", suspend)
            return True, f"Queued: {jobid} until {suspend}"

        elif parts[0] == "alloc":
            error, result = self.mem.alloc(mint(parts[1], 0))
            return True, result

        elif parts[0] == "free":
            error, result = self.mem.free(mint(parts[1], 0))
            return True, result

        elif parts[0] == "write":
            error, result = self.mem.write(
                mint(parts[1], 0),
                [int(p) for p in parts[2:]]
            )
            return True, result

        elif parts[0] == "read":
            error, result = self.mem.read(
                mint(parts[1], 0),
                mint(parts[2], 0)
            )
            return True, result

        elif parts[0] == "bwrite":
            error, result = self.mem.write(
                mint(parts[1], 0),
                [ord(p) for p in bencode(parts[2], True)]
            )
            return True, result

        elif parts[0] == "bread":
            error, result = self.mem.read(
                mint(parts[1], 0),
                mint(parts[2], 0)
            )
            value = "".join(chr(r) for r in result)
            _, final = bdecode(value)
            return True, final

        elif parts[0] == "quit":
            return False, "quit"

        return False, None

    def execute(self, data, sim=True):
        display, result = self.eval(data)
        if display:
            if sim:
                return False, result

            else:
                print(result)
                print()

        elif result == "quit":
            if sim:
                return True, None

            return True

        if sim:
            return False, None

        return False

    def process(self, sim=True):
        ts = now()

        mentry = self.sched.pop()
        if not isinstance(mentry, Nil):
            entry = mentry.value
            until = entry["until"]
            action = entry["action"]
            jobid = entry["id"]
            if not sim and until > ts:
                self.sched.push(action, until, jobid)

            else:
                result = self.execute(action, sim)
                if sim:
                    return result

                return True

        if sim:
            return False, None

        return False

    def loop(self):
        cache = None
        while True:
            ran = self.process(False)
            if ran:
                continue

            data = self.read()
            done = self.execute(data, False)
            if done:
                break

    def start(self):
        self.loop()
