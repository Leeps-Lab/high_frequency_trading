from collections import deque


class MessageRegistry:

    def __init__(self, factory):
        self.message_factory = factory
        self.outgoing_messages = deque()

    def __call__(self, message_type, **kwargs):
        message = self.message_factory.get_message(message_type, **kwargs)
        self.outgoing_messages.append(message)
    
    def __bool__(self):
        return True if len(self.outgoing_messages) else False
    
    def __str__(self):
        return '\n'.join(str(m) for m in self.outgoing_messages)

    def pop(self):
        if len(self.outgoing_messages):
            return self.outgoing_messages.pop()