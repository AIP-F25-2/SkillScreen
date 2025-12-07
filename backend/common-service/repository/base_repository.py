class BaseRepository:
    def __init__(self, session_or_uow):
        if hasattr(session_or_uow, 'session'):
            self.uow = session_or_uow
            self.session = session_or_uow.session
        else:
            self.uow = None
            self.session = session_or_uow
