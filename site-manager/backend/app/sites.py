import uuid

from fastapi import APIRouter
from sqlmodel import Field, Relationship, SQLModel, select

from .dependencies import SessionDep, get_session
from .links import SiteAccessRelationship
from .users import UserInDb, User


class Site(SQLModel, table=True):
    site_id: uuid.UUID = Field(primary_key=True)
    users: list[UserInDb] = Relationship(link_model=SiteAccessRelationship)


sites = APIRouter(prefix="/sites")


@sites.get("/")
def get_all_sites(session: SessionDep) -> list[Site]:
    return [site for site in session.exec(select(Site))]


print(get_all_sites(session=get_session().__next__()))
