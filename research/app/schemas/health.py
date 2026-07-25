from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status")
    project: str = Field(..., description="Project name")
    database: str = Field(..., description="Database connectivity status")
    redis: str = Field(..., description="Redis connectivity status")
