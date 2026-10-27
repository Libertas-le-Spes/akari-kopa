class People:
    def __init__(self, me: str):
        self.me = me

    def from_me(self, said: dict) -> bool:
        author = said["author"]
        return author is not None and author.get("login") == self.me

    def from_others(self, said: dict) -> bool:
        author = said["author"]
        if author is None:
            return False
        return author["login"] != self.me and author["__typename"] != "Bot"
