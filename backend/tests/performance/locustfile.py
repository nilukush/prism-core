"""
Performance and load tests using Locust.
Tests API endpoints under various load conditions.
"""

import random
import json
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import logging

logger = logging.getLogger(__name__)


class PrismUser(HttpUser):
    """
    Simulates a PRISM platform user performing various operations.
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.user_id = None
        self.workspace_ids = []
        self.agent_ids = []
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Register and login
        self.register_and_login()
        # Get initial data
        self.fetch_initial_data()
    
    def register_and_login(self):
        """Register a new user and login."""
        # Generate unique user data
        username = f"loadtest_{random.randint(1000000, 9999999)}"
        
        # Register
        register_data = {
            "email": f"{username}@loadtest.com",
            "username": username,
            "full_name": f"Load Test User {username}",
            "password": "LoadTest123!",
            "organization_id": "test-org-id"  # Would be pre-created
        }
        
        with self.client.post(
            "/api/v1/auth/register",
            json=register_data,
            catch_response=True
        ) as response:
            if response.status_code != 201:
                response.failure(f"Registration failed: {response.text}")
                return
            response.success()
        
        # Login
        login_data = {
            "username": register_data["email"],
            "password": register_data["password"]
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            data=login_data,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Login failed: {response.text}")
                return
            
            data = response.json()
            self.token = data["access_token"]
            self.client.headers["Authorization"] = f"Bearer {self.token}"
            response.success()
    
    def fetch_initial_data(self):
        """Fetch initial data like workspaces and agents."""
        # Get user profile
        with self.client.get("/api/v1/users/me", catch_response=True) as response:
            if response.status_code == 200:
                self.user_id = response.json()["id"]
                response.success()
            else:
                response.failure("Failed to get user profile")
        
        # Get workspaces
        with self.client.get("/api/v1/workspaces", catch_response=True) as response:
            if response.status_code == 200:
                workspaces = response.json()["data"]
                self.workspace_ids = [w["id"] for w in workspaces]
                response.success()
            else:
                response.failure("Failed to get workspaces")
        
        # Get agents
        with self.client.get("/api/v1/agents", catch_response=True) as response:
            if response.status_code == 200:
                agents = response.json()["data"]
                self.agent_ids = [a["id"] for a in agents]
                response.success()
            else:
                response.failure("Failed to get agents")
    
    @task(10)
    def list_workspaces(self):
        """List workspaces - most common operation."""
        self.client.get("/api/v1/workspaces?limit=25")
    
    @task(8)
    def view_workspace(self):
        """View a specific workspace."""
        if self.workspace_ids:
            workspace_id = random.choice(self.workspace_ids)
            self.client.get(f"/api/v1/workspaces/{workspace_id}")
    
    @task(6)
    def list_agents(self):
        """List AI agents."""
        params = {
            "limit": 25,
            "type": random.choice(["conversational", "analytical", None])
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        self.client.get("/api/v1/agents", params=params)
    
    @task(5)
    def view_agent(self):
        """View a specific agent."""
        if self.agent_ids:
            agent_id = random.choice(self.agent_ids)
            self.client.get(f"/api/v1/agents/{agent_id}")
    
    @task(3)
    def execute_agent(self):
        """Execute an AI agent."""
        if not self.agent_ids:
            return
        
        agent_id = random.choice(self.agent_ids)
        execution_data = {
            "input_data": {
                "message": f"Test query {random.randint(1, 1000)}",
                "context": {"session_id": f"session_{random.randint(1000, 9999)}"}
            },
            "parameters": {
                "temperature": round(random.uniform(0.1, 1.0), 1),
                "max_tokens": random.choice([100, 500, 1000])
            }
        }
        
        with self.client.post(
            f"/api/v1/agents/{agent_id}/execute",
            json=execution_data,
            catch_response=True
        ) as response:
            if response.status_code == 202:
                response.success()
            else:
                response.failure(f"Agent execution failed: {response.text}")
    
    @task(4)
    def get_analytics(self):
        """Get usage analytics."""
        time_range = random.choice(["last_24_hours", "last_7_days", "last_30_days"])
        self.client.get(f"/api/v1/analytics/usage?time_range={time_range}")
    
    @task(2)
    def create_workspace(self):
        """Create a new workspace."""
        workspace_data = {
            "name": f"Test Workspace {random.randint(1000, 9999)}",
            "description": "Created during load testing",
            "settings": {
                "theme": random.choice(["light", "dark"]),
                "notifications": random.choice([True, False])
            }
        }
        
        with self.client.post(
            "/api/v1/workspaces",
            json=workspace_data,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                workspace_id = response.json()["id"]
                self.workspace_ids.append(workspace_id)
                response.success()
            else:
                response.failure(f"Workspace creation failed: {response.text}")
    
    @task(1)
    def create_agent(self):
        """Create a new AI agent."""
        if not self.workspace_ids:
            return
        
        agent_data = {
            "name": f"Test Agent {random.randint(1000, 9999)}",
            "description": "Created during load testing",
            "type": random.choice(["conversational", "analytical"]),
            "workspace_id": random.choice(self.workspace_ids),
            "config": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 500
            },
            "capabilities": ["conversation", "analysis"]
        }
        
        with self.client.post(
            "/api/v1/agents",
            json=agent_data,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                agent_id = response.json()["id"]
                self.agent_ids.append(agent_id)
                response.success()
            else:
                response.failure(f"Agent creation failed: {response.text}")
    
    @task(2)
    def search_users(self):
        """Search for users."""
        search_term = random.choice(["test", "load", "user", "dev"])
        self.client.get(f"/api/v1/users?search={search_term}&limit=10")
    
    @task(1)
    def update_profile(self):
        """Update user profile."""
        if not self.user_id:
            return
        
        update_data = {
            "full_name": f"Updated User {random.randint(1000, 9999)}",
            "preferences": {
                "theme": random.choice(["light", "dark", "auto"]),
                "notifications": {
                    "email": random.choice([True, False]),
                    "in_app": True
                }
            }
        }
        
        self.client.patch(f"/api/v1/users/{self.user_id}", json=update_data)


class AdminUser(PrismUser):
    """
    Simulates an admin user with additional permissions.
    """
    
    weight = 1  # 1 admin for every 10 regular users
    
    @task(5)
    def view_all_users(self):
        """Admin viewing all users."""
        self.client.get("/api/v1/users?limit=50")
    
    @task(3)
    def view_organization_analytics(self):
        """View organization-wide analytics."""
        self.client.get("/api/v1/analytics/usage?aggregation=daily")
        self.client.get("/api/v1/analytics/performance")
    
    @task(2)
    def manage_roles(self):
        """Manage user roles."""
        # This would assign/remove roles in a real scenario
        pass


class MobileUser(PrismUser):
    """
    Simulates a mobile app user with different behavior patterns.
    """
    
    weight = 3  # 3 mobile users for every 10 regular users
    wait_time = between(2, 5)  # Mobile users interact less frequently
    
    @task(15)
    def quick_workspace_check(self):
        """Quick check of workspace list."""
        self.client.get("/api/v1/workspaces?limit=10")
    
    @task(10)
    def view_recent_agents(self):
        """View recently used agents."""
        self.client.get("/api/v1/agents?limit=5&sort_by=updated_at")
    
    @task(5)
    def execute_quick_query(self):
        """Execute a quick agent query."""
        if self.agent_ids:
            # Mobile users typically use simpler queries
            agent_id = random.choice(self.agent_ids[:3] if len(self.agent_ids) > 3 else self.agent_ids)
            execution_data = {
                "input_data": {"message": "Quick mobile query"},
                "parameters": {"max_tokens": 100}
            }
            self.client.post(f"/api/v1/agents/{agent_id}/execute", json=execution_data)


# Event handlers for reporting

@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        '--test-duration',
        type=int,
        default=300,
        help='Duration of the test in seconds'
    )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    if isinstance(environment.runner, MasterRunner):
        logger.info("Starting distributed load test")
    else:
        logger.info(f"Starting load test with {environment.parsed_options.num_users} users")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, **kwargs):
    if response_time > 1000:  # Log slow requests (> 1 second)
        logger.warning(
            f"Slow request: {request_type} {name} took {response_time}ms"
        )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("Load test completed")
    
    # Calculate and log statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failed requests: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time}ms")
    logger.info(f"RPS: {stats.total.current_rps}")