from repositories.organization_repository import OrganizationRepository

class OrganizationService:

    def __init__(self, uow):
        self.repo = OrganizationRepository(uow)

    def create(self, payload: dict):
        data = {
            "name": payload["name"],
            "domain": payload.get("domain"),
            "settings": payload.get("settings"),
        }
        return self.repo.create(data)

    def get_all(self):
        return self.repo.get_all()

    def get_by_id(self, org_id: str):
        return self.repo.get_by_id(org_id)

    def update(self, org_id: str, payload: dict):
        return self.repo.update(org_id, payload)

    def delete(self, org_id: str):
        return self.repo.delete(org_id)
