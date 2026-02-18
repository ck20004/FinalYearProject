from fastapi import APIRouter, HTTPException, Depends
import httpx
import base64
import os
import uuid
from typing import List

from models.schemas import GitHubRepoRequest, GitHubRepoResponse, FileContent, ErrorResponse
from services.session_manager import session_manager
from redis_db.connection import redis_manager

router = APIRouter()
# session_manager = session_manager()

async def get_github_headers():
    """Get GitHub API headers with authentication"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="GitHub token not configured")
    
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

@router.post("/analyze-repo", response_model=GitHubRepoResponse)
async def analyze_repository(request: GitHubRepoRequest):
    """
    Analyze a GitHub repository for architecture-relevant information.
    Migrated from your existing Express.js implementation.
    """
    try:
        # Ensure Redis is connected
        if not redis_manager.is_connected():
            await redis_manager.connect()
        

        # Extract owner and repo from URL
        import re
        match = re.search(r'github\.com/([^/]+)/([^/]+)', request.repo_url)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid GitHub repo URL")
        
        owner = match.group(1)
        repo = match.group(2).replace('.git', '')
        
        headers = await get_github_headers()
        
        async with httpx.AsyncClient() as client:
            # Fetch repo metadata
            repo_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers
            )
            
            if repo_response.status_code != 200:
                raise HTTPException(
                    status_code=repo_response.status_code,
                    detail=f"Failed to fetch repository: {repo_response.text}"
                )
            
            repo_data = repo_response.json()
            branch = request.branch or repo_data["default_branch"]
            
            # Fetch file tree (recursive)
            tree_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
                headers=headers
            )
            
            if tree_response.status_code != 200:
                raise HTTPException(
                    status_code=tree_response.status_code,
                    detail="Failed to fetch repository tree"
                )
            
            tree_data = tree_response.json()
            
            # Filter and limit files (for now, let's limit to important files)
            important_extensions = {'.tf', '.yml', '.yaml', '.json', '.py', '.js', '.ts', '.md', '.dockerfile', '.ipynb'}
            important_files = ['requirements.txt', 'package.json', 'pom.xml', 'Gemfile', 'Cargo.toml']
            
            files = [
                item for item in tree_data["tree"]
                if item["type"] == "blob" and (
                    any(item["path"].lower().endswith(ext) for ext in important_extensions) or
                    any(important_file in item["path"].lower() for important_file in important_files)
                )
            ]
            
            # Limit to 50 files to avoid overwhelming the system
            files = files[:50]
            
            # Fetch file contents
            file_contents = []
            for file in files:
                try:
                    content_response = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}/contents/{file['path']}",
                        headers=headers
                    )
                    
                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        if content_data.get("content"):
                            decoded_content = base64.b64decode(content_data["content"]).decode('utf-8')
                            file_contents.append(FileContent(
                                path=file["path"],
                                content=decoded_content
                            ))
                except Exception as e:
                    # Skip files that can't be decoded or fetched
                    print(f"Skipping file {file['path']}: {e}")
                    continue
            
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Store in Redis session manager
            session_data = {
                "type": "github_analysis",
                "repo_data": repo_data,
                "files": [fc.dict() for fc in file_contents],
                "analysis_complete": True
            }
            
            success = await session_manager.store_session(session_id, session_data)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to store session data")
            
            return GitHubRepoResponse(
                owner_name=repo_data["owner"]["login"],
                project_name=repo_data["name"],
                repo_url=repo_data["html_url"],
                project_description=repo_data.get("description"),
                files=file_contents,
                session_id=session_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/analyze-repo/{session_id}")
async def get_analysis_result(session_id: str):
    """Get previously analyzed repository data"""
    # Ensure Redis is connected
    if not redis_manager.is_connected():
        await redis_manager.connect()
    
    session_data = await session_manager.get_session(session_id)
    
    if not session_data or session_data.get("type") != "github_analysis":
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_data