import uuid

from sqlmodel import Field, SQLModel


class SiteAccessRelationship(SQLModel, table=True):
    site_id: uuid.UUID = Field(primary_key=True, foreign_key="site.site_id")
    username: str = Field(primary_key=True, foreign_key="userindb.username")
