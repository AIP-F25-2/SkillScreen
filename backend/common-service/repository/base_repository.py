class BaseRepository:
    def __init__(self, uow):
        self.uow = uow
        self.session = uow.session
