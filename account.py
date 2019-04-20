class Account:
    id = ''
    username = ''
    password = ''
    provider = ''
    cookies_path = ''
    pin_protected = True

    def __init__(self, id, username, password, provider, cookies_path, pin_protected=True):
        self.id = id
        self.username = username
        self.password = password
        self.provider = provider
        self.cookies_path = cookies_path
        self.pin_protected = pin_protected

    def is_valid(self):
        if self.username and self.password and self.provider:
            return True
        else:
            return False
