"""
GitHub Service for Causal Affect Platform

Pushes generated MVP code to GitHub repositories.
Uses PyGithub with a Personal Access Token (PAT).
"""

import logging
import os
import re
from typing import List, Tuple

from github import Github, GithubException, InputGitTreeElement

logger = logging.getLogger(__name__)


class GitHubService:
    """Creates GitHub repositories and pushes generated MVP files."""

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.org = os.getenv("GITHUB_ORG")
        self.enabled = bool(self.token and self.org)
        self._client = None

        if self.enabled:
            logger.info("✅ GitHub service initialised")
        else:
            logger.warning("⚠️  GITHUB_TOKEN or GITHUB_ORG not set — GitHub push disabled")

    @property
    def client(self) -> Github:
        if self._client is None:
            self._client = Github(self.token)
        return self._client

    @staticmethod
    def slugify(name: str, max_len: int = 60) -> str:
        """Convert a string to a valid GitHub repo name."""
        slug = name.lower().replace(" ", "-").replace("/", "-")
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug[:max_len] or "mvp-build"

    def create_repository(self, name: str, description: str = "") -> dict:
        """Create a new GitHub repo. Returns {full_name, html_url, clone_url}."""
        if not self.enabled:
            raise RuntimeError("GitHub not configured")

        user = self.client.get_user()
        try:
            repo = user.create_repo(
                name=name,
                description=description[:350] if description else "",
                private=False,
                auto_init=True,
            )
        except GithubException as e:
            if e.status == 422:  # Repo already exists
                repo = self.client.get_repo(f"{self.org}/{name}")
                logger.info(f"GitHub repo already exists: {repo.full_name}")
            else:
                raise

        logger.info(f"GitHub repo ready: {repo.html_url}")
        return {
            "full_name": repo.full_name,
            "html_url": repo.html_url,
            "clone_url": repo.clone_url,
        }

    def push_files(
        self,
        repo_name: str,
        files: List[Tuple[str, str]],
        commit_message: str = "Initial MVP build",
    ) -> str:
        """Push files to a GitHub repo.

        Args:
            repo_name: Name of the repo (under self.org).
            files: List of (file_path, content) tuples.
            commit_message: Git commit message.

        Returns:
            Commit SHA.
        """
        if not self.enabled:
            raise RuntimeError("GitHub not configured")

        repo = self.client.get_repo(f"{self.org}/{repo_name}")

        default_branch = repo.default_branch
        ref = repo.get_git_ref(f"heads/{default_branch}")
        base_sha = ref.object.sha
        base_tree = repo.get_git_tree(base_sha)

        tree_elements = []
        for path, content in files:
            tree_elements.append(
                InputGitTreeElement(
                    path=path,
                    mode="100644",
                    type="blob",
                    content=content,
                )
            )

        new_tree = repo.create_git_tree(tree_elements, base_tree)
        parent = repo.get_git_commit(base_sha)
        commit = repo.create_git_commit(commit_message, new_tree, [parent])
        ref.edit(commit.sha)

        logger.info(f"Pushed {len(files)} files to {repo.full_name} ({commit.sha[:8]})")
        return commit.sha
