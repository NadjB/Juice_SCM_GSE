from lppinstru.discovery import Discovery


class Disco_Driver(Discovery):
    def __init__(self, card=-1):
        super(self).__init__(card=card)

    def turn_on(self):
        self.digital_io = 1

    def turn_off(self):
        self.digital_io = 0
