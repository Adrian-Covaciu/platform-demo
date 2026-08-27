from enum import Enum

from pydantic import BaseModel, Field, model_validator


class WorkloadType(str, Enum):
    API = "api"
    WORKER = "worker"
    CRONJOB = "cronjob"


class Resource(BaseModel):
    name: str
    type: str
    config: dict = Field(default_factory=dict)


class Component(BaseModel):
    name: str
    workload_type: WorkloadType
    schedule: str | None = None


class Service(BaseModel):
    name: str
    components: list[Component] = Field(min_length=1)
    resources: list[Resource] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_unique_resources(self) -> "Service":
        seen = set()
        for r in self.resources:
            if r.name in seen:
                raise ValueError(f"Duplicate resource name '{r.name}' in service '{self.name}'")
            seen.add(r.name)
        return self

class Retailer(BaseModel):
    name: str
    services: list[Service] = Field(default_factory=list)
