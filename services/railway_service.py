"""
Railway Service for Causal Affect Platform

Programmatic deployment of MVPs to Railway via GraphQL API.
Follows the same pattern as stripe_service.py / s3_service.py.
"""

import logging
import os
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

RAILWAY_API_URL = "https://backboard.railway.com/graphql/v2"


class RailwayService:
    """Manages Railway project/service creation and deployment."""

    def __init__(self):
        self.api_token = os.getenv("RAILWAY_TOKEN")
        self.enabled = bool(self.api_token)

        if self.enabled:
            logger.info("✅ Railway service initialised")
        else:
            logger.warning("⚠️  RAILWAY_TOKEN not set — auto-deploy disabled")

    def _gql(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a Railway GraphQL request."""
        resp = requests.post(
            RAILWAY_API_URL,
            json={"query": query, "variables": variables or {}},
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        if "errors" in body:
            raise RuntimeError(f"Railway API error: {body['errors']}")
        return body.get("data", {})

    # ------------------------------------------------------------------
    # Project management
    # ------------------------------------------------------------------

    def create_project(self, name: str) -> Dict[str, Any]:
        """Create a new Railway project. Returns {id, name}."""
        if not self.enabled:
            raise RuntimeError("Railway not configured")
        data = self._gql(
            """
            mutation($name: String!) {
                projectCreate(input: { name: $name }) {
                    id
                    name
                }
            }
            """,
            {"name": name},
        )
        project = data.get("projectCreate", {})
        logger.info(f"Created Railway project: {project.get('id')}")
        return project

    def create_service(self, project_id: str, name: str) -> Dict[str, Any]:
        """Create a service within a project. Returns {id, name}."""
        if not self.enabled:
            raise RuntimeError("Railway not configured")
        data = self._gql(
            """
            mutation($projectId: String!, $name: String!) {
                serviceCreate(input: { projectId: $projectId, name: $name }) {
                    id
                    name
                }
            }
            """,
            {"projectId": project_id, "name": name},
        )
        return data.get("serviceCreate", {})

    def get_default_environment(self, project_id: str) -> Optional[str]:
        """Get the default (production) environment ID for a project."""
        if not self.enabled:
            return None
        data = self._gql(
            """
            query($projectId: String!) {
                project(id: $projectId) {
                    environments {
                        edges {
                            node {
                                id
                                name
                            }
                        }
                    }
                }
            }
            """,
            {"projectId": project_id},
        )
        edges = data.get("project", {}).get("environments", {}).get("edges", [])
        if edges:
            return edges[0]["node"]["id"]
        return None

    # ------------------------------------------------------------------
    # Deployment
    # ------------------------------------------------------------------

    def deploy_from_image(self, service_id: str, image: str, environment_id: str) -> Dict[str, Any]:
        """Trigger a deployment from a Docker image."""
        if not self.enabled:
            raise RuntimeError("Railway not configured")
        data = self._gql(
            """
            mutation($serviceId: String!, $environmentId: String!, $image: String!) {
                serviceInstanceDeploy(
                    serviceId: $serviceId,
                    environmentId: $environmentId,
                    input: { image: $image }
                ) {
                    id
                    status
                }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id, "image": image},
        )
        return data.get("serviceInstanceDeploy", {})

    def get_service_domain(self, service_id: str, environment_id: str) -> Optional[str]:
        """Get the public domain for a deployed service."""
        if not self.enabled:
            return None
        data = self._gql(
            """
            query($serviceId: String!, $environmentId: String!) {
                domains(serviceId: $serviceId, environmentId: $environmentId) {
                    serviceDomains {
                        domain
                    }
                }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        domains = data.get("domains", {}).get("serviceDomains", [])
        if domains:
            return f"https://{domains[0]['domain']}"
        return None

    def generate_domain(self, service_id: str, environment_id: str) -> Optional[str]:
        """Generate a Railway-provided domain for a service."""
        if not self.enabled:
            return None
        data = self._gql(
            """
            mutation($serviceId: String!, $environmentId: String!) {
                serviceDomainCreate(
                    input: { serviceId: $serviceId, environmentId: $environmentId }
                ) {
                    domain
                }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        domain = data.get("serviceDomainCreate", {}).get("domain")
        return f"https://{domain}" if domain else None

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_deployment_status(self, deployment_id: str) -> str:
        """Return deployment status: SUCCESS, BUILDING, DEPLOYING, FAILED, etc."""
        if not self.enabled:
            return "UNKNOWN"
        data = self._gql(
            """
            query($id: String!) {
                deployment(id: $id) {
                    status
                }
            }
            """,
            {"id": deployment_id},
        )
        return data.get("deployment", {}).get("status", "UNKNOWN")
