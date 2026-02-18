from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum

class StatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    error = "error"

# GitHub Models
class GitHubRepoRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None

class FileContent(BaseModel):
    path: str
    content: str

class GitHubRepoResponse(BaseModel):
    owner_name: str
    project_name: str
    repo_url: str
    project_description: Optional[str]
    files: List[FileContent]
    session_id: str

# Architecture Generation Models
class ArchitectureRequest(BaseModel):
    prompt: str
    region: Optional[str] = "us-east-1"
    max_cost: Optional[float] = None
    expected_total_users: int
    usage_pattern: str
    storage: int
    concurrent_users: int
    daily_requests: int
    latency_requirements: int
    constraints: str

class AWSResource(BaseModel):
    type: str
    name: str
    properties: Dict[str, Any]

class ResourceConnection(BaseModel):
    from_resource: str
    to_resource: str
    connection_type: str

class ArchitectureResponse(BaseModel):
    session_id: str
    status: StatusEnum
    architecture: Optional[Dict[str, Any]] = None
    # terraform_code: Optional[str] = None
    # diagram_mermaid: Optional[str] = None
    suggestions: Optional[List[str]] = None

class OptimizationRequest(BaseModel):
    description: str = "Scan and optimize the configured AWS account."

# AWS Integration Models
class AWSCredentialsRequest(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    region: Optional[str] = "us-east-1"
    session_token: Optional[str] = None

class AWSResourcesResponse(BaseModel):
    vpcs: List[Dict[str, Any]]
    ec2_instances: List[Dict[str, Any]]
    databases: List[Dict[str, Any]]
    other_resources: List[Dict[str, Any]]
    session_id: str

# Chat Models
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    session_id: str

# Optimization Models
class GetOptimizationResultRequest(BaseModel):
    session_id: str

class OptimizationResponse(BaseModel):
    suggestions: List[str]
    session_id: str

# Report Models
class ReportResponse(BaseModel):
    report_text: str
    diagram_url: Optional[str] = None
    terraform_archive: Optional[str] = None
    session_id: str

# Common Response Models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    status: StatusEnum