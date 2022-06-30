# generated by datamodel-codegen:
#   filename:  schema.json
#   timestamp: 2022-06-30T18:30:50+00:00

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Extra, Field, constr


class AccessRight(Enum):
    open = 'open'
    embargoed = 'embargoed'


class Community(BaseModel):
    identifier: Optional[str] = Field(None, description='The community identifier', title='Identifier')


class Type(Enum):
    ContactPerson = 'ContactPerson'
    DataCollector = 'DataCollector'
    DataCurator = 'DataCurator'
    DataManager = 'DataManager'
    Distributor = 'Distributor'
    Editor = 'Editor'
    HostingInstitution = 'HostingInstitution'
    Other = 'Other'
    Producer = 'Producer'
    ProjectLeader = 'ProjectLeader'
    ProjectManager = 'ProjectManager'
    ProjectMember = 'ProjectMember'
    RegistrationAgency = 'RegistrationAgency'
    RegistrationAuthority = 'RegistrationAuthority'
    RelatedPerson = 'RelatedPerson'
    Researcher = 'Researcher'
    ResearchGroup = 'ResearchGroup'
    RightsHolder = 'RightsHolder'
    Sponsor = 'Sponsor'
    Supervisor = 'Supervisor'
    WorkPackageLeader = 'WorkPackageLeader'


class Contributor(BaseModel):
    class Config:
        extra = Extra.forbid

    affiliation: str = Field(
        ...,
        description='Affiliation for the purpose of this specific record.',
        title='Affiliation',
    )
    name: str = Field(
        ...,
        description='Full name of person or organisation. Personal name format: family, given.',
        title='Full name',
    )
    orcid: Optional[constr(regex=r'(\d{4}-){3}\d{4}')] = Field(
        None, description='ORCID identifier for contributor.', title='ORCID'
    )
    type: Type = Field(..., title='Contribution type')


class Creator(BaseModel):
    class Config:
        extra = Extra.forbid

    affiliation: str = Field(
        ...,
        description='Affiliation for the purpose of this specific record.',
        title='Affiliation',
    )
    name: str = Field(
        ...,
        description='Full name of person or organisation. Personal name format: family, given.',
        title='Full name',
    )
    orcid: Optional[constr(regex=r'(\d{4}-){3}\d{4}')] = Field(
        None, description='ORCID identifier for creator.', title='ORCID'
    )


class RelatedIdentifier(BaseModel):
    identifier: str = Field(
        ...,
        description='Identifier of the related publication or dataset.',
        title='Identifier',
    )
    relation: Union[
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
    ] = Field(
        ...,
        description='The type of relationship between this item and the related item.',
        title='Relationship type',
    )
    resource_type: Optional[
        Union[
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
            Any,
        ]
    ] = Field(
        None,
        description='Resource type of the related identifier.',
        title='Resource type',
    )


class ResourceType(BaseModel):
    class Config:
        extra = Extra.forbid

    openaire_subtype: Optional[str] = Field(
        None, description='OpenAIRE-specific resource type.', title='OpenAIRE subtype'
    )
    subtype: Optional[str] = Field(None, description='Specific resource type.', title='Subtype')
    type: str = Field(..., description='General resource type.', title='General resource type')


class Subject(BaseModel):
    class Config:
        extra = Extra.forbid

    identifier: Optional[str] = Field(
        None,
        description='Subjects term identifier (e.g., a URL).',
        title='Term identifier',
    )
    term: Optional[str] = Field(None, description='Subject term value.', title='Subject term')


class UploadType(Enum):
    publication = 'publication'
    poster = 'poster'
    presentation = 'presentation'
    dataset = 'dataset'
    image = 'image'
    video = 'video'
    software = 'software'
    lesson = 'lesson'
    physicalobject = 'physicalobject'
    other = 'other'


class ZenodoDatasetsSchemaForCzNetV100(BaseModel):
    access_conditions: Optional[str] = Field(
        None,
        description='Conditions under which access is given if record is restricted.',
        title='Access conditions',
    )
    access_right: AccessRight = Field(..., description='Access right for record', title='Access right')
    communities: Optional[List[Community]] = Field(
        None,
        description='List of community identifiers.',
        title='Communities',
        unique_items=True,
    )
    contributors: Optional[List[Contributor]] = Field(
        None, description='Contributors in order of importance.', title='Contributors'
    )
    creators: Optional[List[Creator]] = Field(
        None, description='Creators of record in order of importance.', title='Creators'
    )
    description: str = Field(
        ...,
        description='Description/abstract for record.',
        title='Description/Abstract',
    )
    embargo_date: Optional[date] = Field(
        None,
        description='Embargo date of record (ISO8601 formatted date)',
        title='Embargo date',
    )
    notes: str = Field(
        ...,
        description='Add metadata associated with funding agency credits for a resource in the format provided. Please separate multiple entries with an empty line.',
        title='Funding Agency Metadata',
    )
    keywords: List[str] = Field(
        ...,
        description='Free text keywords.',
        min_items=2,
        title='Keywords',
        unique_items=True,
    )
    license: Union[
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
        Any,
    ] = Field(..., description='License for embargoed/open access content.', title='License')
    publication_date: Optional[date] = Field(None, description='', title='Publication date')
    references: Optional[List[str]] = Field(
        None,
        description='Raw textual references for related publications and datasets when identifier is not known.',
        title='References',
    )
    related_identifiers: Optional[List[RelatedIdentifier]] = Field(
        None,
        description='Identifiers of related publications and datasets.',
        title='Related identifiers',
    )
    resource_type: Optional[ResourceType] = Field(None, description='Record resource type.', title='Resource type')
    subjects: Optional[List[Subject]] = Field(
        None,
        description='Subjects from a taxonomy or controlled vocabulary.',
        title='Subjects from specific vocabularies',
    )
    title: str = Field(..., description='Descriptive title for the record.', title='Title')
    version: Optional[str] = Field(
        None,
        description='Record version tag. Mostly relevant for software and dataset uploads. Any string will be accepted, but semantically-versioned tag is recommended.',
        title='Version',
    )
    upload_type: Optional[UploadType] = Field('dataset', description='Record upload type.')
