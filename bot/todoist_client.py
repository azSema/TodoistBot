from todoist_api_python.api import TodoistAPI
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, List, Dict
import aiohttp


@dataclass
class TaskInfo:
    content: str
    project_name: str
    completed_at: Optional[datetime] = None
    due_date: Optional[str] = None


class TodoistClient:
    def __init__(self, token: str):
        self.token = token
        self.api = TodoistAPI(token)
    
    async def verify_token(self) -> bool:
        try:
            self.api.get_projects()
            return True
        except Exception:
            return False
    
    async def get_projects(self) -> Dict[str, str]:
        projects = self.api.get_projects()
        return {p.id: p.name for p in projects}
    
    async def get_active_tasks(self) -> List[TaskInfo]:
        tasks = self.api.get_tasks()
        projects = await self.get_projects()
        
        return [
            TaskInfo(
                content=t.content,
                project_name=projects.get(t.project_id, "Inbox"),
                due_date=t.due.string if t.due else None
            )
            for t in tasks
        ]
    
    async def get_completed_tasks(self, since: datetime) -> List[TaskInfo]:
        headers = {"Authorization": f"Bearer {self.token}"}
        since_str = since.strftime("%Y-%m-%dT%H:%M:%S")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.todoist.com/sync/v9/completed/get_all",
                headers=headers,
                params={"since": since_str}
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
        
        projects = await self.get_projects()
        
        return [
            TaskInfo(
                content=item["content"],
                project_name=projects.get(item.get("project_id", ""), "Inbox"),
                completed_at=datetime.fromisoformat(item["completed_at"].replace("Z", "+00:00"))
            )
            for item in data.get("items", [])
        ]
    
    async def get_today_completed(self) -> List[TaskInfo]:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.get_completed_tasks(today)
    
    async def get_week_completed(self) -> List[TaskInfo]:
        week_ago = datetime.now() - timedelta(days=7)
        return await self.get_completed_tasks(week_ago)
    
    async def get_month_completed(self) -> List[TaskInfo]:
        month_ago = datetime.now() - timedelta(days=30)
        return await self.get_completed_tasks(month_ago)
    
    async def add_task(self, content: str, project_id: Optional[str] = None) -> bool:
        try:
            kwargs = {"content": content}
            if project_id:
                kwargs["project_id"] = project_id
            self.api.add_task(**kwargs)
            return True
        except Exception:
            return False
    
    async def close_task(self, task_id: str) -> bool:
        try:
            self.api.close_task(task_id)
            return True
        except Exception:
            return False
