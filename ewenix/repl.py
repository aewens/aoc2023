from ewenix.scheduler import Scheduler
from ewenix.monad import Nil
from ewenix.util import now, mint

class REPL:
    def __init__(self):
        self.sched = Scheduler()

    def read(self):
        return input("ewenix> ")

    def eval(self, data):
        commands = dict()
        commands["help"] = "Display this message"
        commands["print"] = "Print back input"
        commands["echo"] = "Print back input with a delay"
        commands["quit"] = "Exit the REPL"

        parts = list()
        cache = ""
        mode = 0
        for i in range(len(data)):
            char = data[i]
            if char == "\"":
                if mode == 0:
                    mode = 2
                    continue

                elif mode == 1:
                    parts.append(cache)
                    cache = ""
                    mode = 0
                    continue

            elif char == " " and mode != 1:
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
