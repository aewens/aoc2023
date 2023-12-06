from ewenix.util import now, mint
from ewenix.monad import Nil
from ewenix.scheduler import Scheduler
from ewenix.algorithms import Memory
from ewenix.encoding import bencode, bdecode

QUIT = "%QUIT%"

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

    def eval(self, data, jobid=None):
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
                    if len(cache) > 0:
                        parts.append(cache)

                    cache = ""
                    mode = 0
                    continue

            elif char == " " and mode not in [1,3]:
                if len(cache) > 0:
                    parts.append(cache)

                cache = ""
                mode = 0
                continue

            elif char == ";" and mode == 3:
                cache = cache + char
                if len(cache) > 0:
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
            if jobid is None:
                jobid = self.sched.get_next_id()

            error, result = self.mem.alloc(mint(parts[1], 0), jobid=jobid)
            return True, result

        elif parts[0] == "free":
            if jobid is None:
                jobid = self.sched.get_next_id()

            error, result = self.mem.free(mint(parts[1], 0), jobid=jobid)
            return True, result

        elif parts[0] == "write":
            if jobid is None:
                jobid = self.sched.get_next_id()

            error, result = self.mem.write(
                mint(parts[1], 0),
                [int(p) for p in parts[2:]],
                jobid=jobid
            )
            return True, result

        elif parts[0] == "read":
            if jobid is None:
                jobid = self.sched.get_next_id()

            error, result = self.mem.read(
                mint(parts[1], 0),
                mint(parts[2], 0),
                jobid=jobid
            )
            return True, result

        elif parts[0] == "bwrite":
            if jobid is None:
                jobid = self.sched.get_next_id()

            error, result = self.mem.write(
                mint(parts[1], 0),
                [ord(p) for p in bencode(parts[2], True)],
                jobid=jobid
            )
            return True, result

        elif parts[0] == "bread":
            if jobid is None:
                jobid = self.sched.get_next_id()

            error, result = self.mem.read(
                mint(parts[1], 0),
                mint(parts[2], 0),
                jobid=jobid
            )
            value = "".join(chr(r) for r in result)
            _, final = bdecode(value)
            return True, final

        elif parts[0] == "run":
            if jobid is None:
                jobid = self.sched.get_next_id()

            index = 1
            results = list()
            command = list()
            while index < len(parts):
                part = parts[index]
                #print(part, index)
                index = index + 1

                if "\"" in part[1:-1]:
                    part = f"@{part}"

                run = False
                if part == ";":
                    run = True

                elif part.endswith(";"):
                    command.append(part[:-1])
                    run = True

                elif index == len(parts):
                    command.append(part)
                    run = True

                if not run:
                    command.append(part)
                    continue

                cmd = " ".join(command)
                cmd = cmd.strip()
                command = list()

                display, result = self.eval(cmd, jobid=jobid)
                results.append((display, result))

            return True, results

        elif parts[0] == "quit":
            return False, QUIT

        return False, None

    def execute(self, data, sim=True, jobid=None):
        display, results = self.eval(data, jobid=jobid)
        if display:
            if sim:
                return False, results

            else:
                if not isinstance(results, list):
                    results = [results]

                for result in results:
                    print(result)

                print()

        elif results == QUIT:
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
