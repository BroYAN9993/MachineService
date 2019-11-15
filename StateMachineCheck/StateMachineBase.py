from queue import Queue

class AbstractIO:
    def __init__(self, q: Queue):
        self.queue = q
        self.current_message = None
    def get_message(self):
        if self.current_message:
            return self.current_message
        while True:
            message = None
            try:
                message = self.queue.get(False)
            except:
                pass
            if message:
                self.current_message = message
                return message
                
    def push_message(self, message):
        self.queue.put(message)

class StateMachine:
    def __init__(self, state, stdin=None, stdout=None, stderr=None):
        self.state = state
        self.stdin = stdin,
        self.stdout = stdout