# from sqlalchemy.orm import Session
# from db.factory import SessionLocal

# class UnitOfWork:
#     def __init__(self):
#         self.session: Session = SessionLocal()

#     def __enter__(self):
#         return self
    
#     def __exit__(self, exc_type, exc_value, traceback):
#         if exc_type:
#             self.rollback()
#         else:
#             self.commit()
#         self.close()

#     def commit(self):
#         self.session.commit()

#     def rollback(self):
#         self.session.rollback()

#     def close(self):
#         self.session.close()