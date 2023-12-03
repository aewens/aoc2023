class REPL:
    def __init__(self):
        pass

    def read(self):
        return input("ewenix> ")

    def eval(self, data):
        commands = dict()
        commands["help"] = "Display this message"
        commands["print"] = "Print back input"
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
            return True, "\n".join(f"{k} - {v}" for k, v in commands.items())

        elif parts[0] == "print":
            return True, " ".join(parts[1:])

        elif parts[0] == "quit":
            return False, "quit"

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

    def loop(self):
        while True:
            data = self.read()
            done = self.execute(data, False)
            if done:
                break

    def start(self):
        self.loop()
