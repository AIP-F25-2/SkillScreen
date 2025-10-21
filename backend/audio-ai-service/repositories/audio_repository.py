from repository.base_repository import BaseRepository
from sqlalchemy import Table, Column, Integer, String, MetaData, select

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String),
)

class UserRepository(BaseRepository):

    def get_all_users(self):
        query = select(users_table)
        result = self.session.execute(query)
        users = result.mappings().all()
        return users

    def get_user_by_id(self, user_id: int):
        query = select(users_table).where(users_table.c.id == user_id)
        result = self.session.execute(query).fetchone()
        return dict(result) if result else None
