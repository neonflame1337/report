class ChannelEntity:
    def __init__(self, id: int, link: str = None, subscribers: int = 0, active: int = 0, approved: int = 0):
        self.id: int = id
        self.link: str = link
        self.subscribers = subscribers
        self.active: int = active
        self.approved: int = approved


class Test:
    def __init__(self, age):
        self.age = age
