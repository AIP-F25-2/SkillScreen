from fastapi import APIRouter, HTTPException
from db import UnitOfWork
from services.organization_service import OrganizationService
from utils.response import create_response
from utilities.logger import init_logger

router = APIRouter(prefix="/organizations", tags=["organizations"])

log = init_logger("user-service")


@router.get("")
def list_orgs():
    with UnitOfWork() as uow:
        service = OrganizationService(uow)
        orgs = service.get_all()
    return create_response({"organizations": orgs})


@router.post("")
def create_org(payload: dict):
    with UnitOfWork() as uow:
        service = OrganizationService(uow)
        org_id = service.create(payload)
    return create_response({"id": org_id})


@router.get("/{org_id}")
def get_org(org_id: str):
    with UnitOfWork() as uow:
        service = OrganizationService(uow)
        org = service.get_by_id(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return create_response({"organization": org})


@router.put("/{org_id}")
def update_org(org_id: str, payload: dict):
    with UnitOfWork() as uow:
        service = OrganizationService(uow)
        updated = service.update(org_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Organization not found")
    return create_response({"organization": updated})


@router.delete("/{org_id}")
def delete_org(org_id: str):
    with UnitOfWork() as uow:
        service = OrganizationService(uow)
        deleted_id = service.delete(org_id)
    if not deleted_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    return create_response({"id": deleted_id})
