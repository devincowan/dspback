import json
import uuid

import requests
from fastapi import Depends, HTTPException
from fastapi_restful.cbv import cbv
from fastapi_restful.inferring_router import InferringRouter
from hsmodels.schemas.resource import ResourceMetadata, ResourceMetadataIn
from requests import Session
from starlette.responses import JSONResponse

from dspback.config import repository_config
from dspback.database.models import RepositoryTokenTable, UserTable
from dspback.database.procedures import delete_submission
from dspback.dependencies import get_current_user, get_db
from dspback.pydantic_schemas import RepositoryType, SubmissionBase
from dspback.routers.submissions import submit_record
from dspback.schemas.earthchem.model import Ecl20
from dspback.schemas.external.model import GenericDatasetSchemaForCzNetDataSubmissionPortalV100
from dspback.schemas.zenodo.model import NotRequiredZenodo, ResponseModelZenodo, ZenodoDatasetsSchemaForCzNetV100

router = InferringRouter()


class MetadataRoutes:
    db: Session = Depends(get_db)
    user: UserTable = Depends(get_current_user)

    request_model = None
    response_model = None
    repository_type = None

    @property
    def access_token(self):
        repository_token: RepositoryTokenTable = self.user.repository_token(self.db, self.repository_type)
        if not repository_token:
            raise HTTPException(
                status_code=403, detail=f"User has not authorized permissions with {self.repository_type}"
            )
        return repository_token.access_token

    async def submit(self, identifier, json_metadata=None):
        if json_metadata is None:
            json_metadata = await self._retrieve_metadata_from_repository(identifier)
        submit_record(self.db, self.repository_type, identifier, self.user, json_metadata)
        return json_metadata

    def __init__(self):
        if self.request_model is None:
            raise ValueError("field request_model must be defined on the child class")
        if self.response_model is None:
            raise ValueError("field response_model must be defined on the child class")
        if self.repository_type is None:
            raise ValueError("field repository_name must be defined on the child class")

        if self.repository_type not in repository_config:
            raise ValueError(f"No configuration found for {self.repository_type}")

        if "read" not in repository_config[self.repository_type]:
            raise ValueError(f"No 'read' value found for {self.repository_type} configuration")
        self.read_url = repository_config[self.repository_type]["read"]

        if "create" not in repository_config[self.repository_type]:
            raise ValueError(f"No 'create' value found for {self.repository_type} configuration")
        self.create_url = repository_config[self.repository_type]["create"]

        if "update" not in repository_config[self.repository_type]:
            raise ValueError(f"No 'update' value found for {self.repository_type} configuration")
        self.update_url = repository_config[self.repository_type]["update"]

        if "delete" not in repository_config[self.repository_type]:
            raise ValueError(f"No 'delete' value found for {self.repository_type} configuration")
        self.delete_url = repository_config[self.repository_type]["delete"]


@cbv(router)
class HydroShareMetadataRoutes(MetadataRoutes):

    request_model = ResourceMetadataIn
    response_model = ResourceMetadata
    repository_type = RepositoryType.HYDROSHARE

    @router.post('/metadata/hydroshare', response_model_exclude_unset=True, response_model=response_model)
    async def create_metadata_repository(self, metadata: request_model):
        response = requests.post(
            self.create_url,
            params={"access_token": self.access_token},
            headers={"Content-Type": "application/json"},
            timeout=15.0,
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        identifier = response.json()["resource_id"]
        # hydroshare doesn't accept all of the metadata on create
        json_metadata = await self.update_metadata(metadata, identifier)

        return JSONResponse(json_metadata, status_code=201)

    @router.put('/metadata/hydroshare/{identifier}', response_model_exclude_unset=True, response_model=response_model)
    async def update_metadata(self, metadata: request_model, identifier):
        response = requests.put(
            self.update_url % identifier,
            data=metadata.json(skip_defaults=True),
            headers={"Content-Type": "application/json"},
            params={"access_token": self.access_token},
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = await self.submit(identifier)
        return json_metadata

    async def _retrieve_metadata_from_repository(self, identifier):
        response = requests.get(self.read_url % identifier, params={"access_token": self.access_token})
        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(response.text)
        return json_metadata

    @router.get('/metadata/hydroshare/{identifier}', response_model_exclude_unset=True, response_model=response_model)
    async def get_metadata_repository(self, identifier):
        json_metadata = await self._retrieve_metadata_from_repository(identifier)
        await self.submit(identifier=identifier, json_metadata=json_metadata)
        # workaround for rendering dict with key/value forms
        if "additional_metadata" in json_metadata:
            as_dict = json_metadata["additional_metadata"]
            json_metadata["additional_metadata"] = [{"key": key, "value": value} for key, value in as_dict.items()]
        return json_metadata

    @router.delete('/metadata/hydroshare/{identifier}')
    async def delete_metadata_repository(self, identifier):
        response = requests.delete(self.delete_url % identifier, params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        delete_submission(self.db, self.repository_type, identifier, self.user)

    @router.put(
        '/submit/hydroshare/{identifier}',
        name="submit",
        response_model_exclude_unset=True,
        response_model=response_model,
    )
    async def submit_repository_record(self, identifier: str):
        json_metadata = await self.submit(identifier)
        return json_metadata


@cbv(router)
class ZenodoMetadataRoutes(MetadataRoutes):

    request_model = ZenodoDatasetsSchemaForCzNetV100
    request_model_update = NotRequiredZenodo
    response_model = ResponseModelZenodo
    repository_type = RepositoryType.ZENODO

    @router.post('/metadata/zenodo', response_model_exclude_unset=True, response_model=response_model)
    async def create_metadata_repository(self, metadata: request_model):
        metadata_json = {"metadata": json.loads(metadata.json(exclude_none=True))}
        response = requests.post(
            self.create_url,
            json=metadata_json,
            params={"access_token": self.access_token},
            headers={"Content-Type": "application/json"},
            timeout=15.0,
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        identifier = response.json()["record_id"]
        json_metadata = await self.get_metadata_repository(identifier)

        return JSONResponse(json_metadata, status_code=201)

    @router.put(
        '/metadata/zenodo/{identifier}',
        response_model_exclude_unset=True,
        response_model=response_model,
    )
    async def update_metadata(self, metadata: request_model_update, identifier):
        existing_metadata = await self.get_metadata_repository(identifier)
        incoming_metadata = metadata.json(skip_defaults=True, exclude_unset=True)
        merged_metadata = {"metadata": {**existing_metadata, **json.loads(incoming_metadata)}}
        response = requests.put(
            self.update_url % identifier,
            json=merged_metadata,
            headers={"Content-Type": "application/json"},
            params={"access_token": self.access_token},
        )

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        # await self.submit(identifier)
        return await self.get_metadata_repository(identifier)

    async def _retrieve_metadata_from_repository(self, identifier):
        response = requests.get(self.read_url % identifier, params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        json_metadata = json.loads(response.text)
        return json_metadata

    @router.get('/metadata/zenodo/{identifier}', response_model_exclude_unset=True, response_model=response_model)
    async def get_metadata_repository(self, identifier):
        json_metadata = await self._retrieve_metadata_from_repository(identifier)
        await self.submit(identifier=identifier, json_metadata=json_metadata)
        return json_metadata["metadata"]

    @router.delete('/metadata/zenodo/{identifier}')
    async def delete_metadata_repository(self, identifier):
        response = requests.delete(self.delete_url % identifier, params={"access_token": self.access_token})

        if response.status_code >= 300:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        delete_submission(self.db, self.repository_type, identifier, self.user)

    @router.put('/submit/zenodo/{identifier}', name="submit", response_model=SubmissionBase)
    async def submit_repository_record(self, identifier: str):
        json_metadata = await self.submit(identifier)
        return json_metadata["metadata"]


@cbv(router)
class EarthChemMetadataRoutes(MetadataRoutes):

    request_model = Ecl20
    request_model_update = Ecl20
    response_model = Ecl20
    repository_type = RepositoryType.EARTHCHEM

    @router.post('/metadata/earthchem')
    async def create_metadata_repository(self, metadata: request_model) -> response_model:
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")

    @router.put('/metadata/earthchem/{identifier}')
    async def update_metadata(self, metadata: request_model_update, identifier) -> response_model:
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")

    async def _retrieve_metadata_from_repository(self, identifier):
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")

    @router.get('/metadata/earthchem/{identifier}')
    async def get_metadata_repository(self, identifier) -> response_model:
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")

    @router.delete('/metadata/earthchem/{identifier}')
    async def delete_metadata_repository(self, identifier):
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")

    @router.put('/submit/earthchem/{identifier}', name="submit")
    async def submit_repository_record(self, identifier: str):
        raise NotImplementedError("EarthChem metadata endpoints are not implemented yet")


@cbv(router)
class ExternalMetadataRoutes(MetadataRoutes):

    request_model = GenericDatasetSchemaForCzNetDataSubmissionPortalV100
    response_model = GenericDatasetSchemaForCzNetDataSubmissionPortalV100
    repository_type = RepositoryType.EXTERNAL

    @router.post('/metadata/external', response_model_exclude_unset=True, response_model=response_model)
    async def create_metadata_repository(self, metadata: request_model):
        metadata.identifier = str(uuid.uuid4())
        return await self.submit(metadata.identifier, metadata.dict())

    @router.put('/metadata/external/{identifier}', response_model_exclude_unset=True, response_model=response_model)
    async def update_metadata(self, metadata: request_model, identifier):
        return await self.submit(identifier, metadata.dict())

    @router.get('/metadata/external/{identifier}', response_model_exclude_unset=True, response_model=response_model)
    async def get_metadata_repository(self, identifier):
        submission = self.user.submission(self.db, identifier)
        metadata_json_str = submission.metadata_json
        metadata_json = json.loads(metadata_json_str)
        return metadata_json

    @router.delete('/metadata/external/{identifier}')
    async def delete_metadata_repository(self, identifier):
        delete_submission(self.db, self.repository_type, identifier, self.user)
