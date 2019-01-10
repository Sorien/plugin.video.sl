class Account:
    id = ''
    username = ''
    password = ''
    provider = ''

    def __init__(self, id, username, password, provider):
        self.id = id
        self.username = username
        self.password = password
        self.provider = provider

    def is_valid(self):
        if self.username and self.password and self.provider:
            return True
        else:
            return False
