import sys
import traceback
from typing import Any, Dict
from datetime import datetime, timedelta
import requests

def register_ci_tools(mcp, github_headers):
    """
    Register MCP tools related to CI pipeline analysis
    """
    @mcp.tool()
    async def analyze_pipeline_results(
        repo_owner: str,
        repo_name: str,
        workflow_id: str = None,
        run_id: str = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Analyze GitHub Actions pipeline results and provide recommendations"""
        try:
            if not all([repo_owner, repo_name]):
                return {
                    "status": "error",
                    "error": "Missing required parameters: repo_owner and repo_name are required"
                }
            # Verify repository access
            try:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}",
                    headers=github_headers
                )
                response.raise_for_status()
            except requests.exceptions.RequestException:
                return {
                    "status": "error",
                    "error": "Repository access verification failed"
                }
            # Get workflow runs
            try:
                if run_id:
                    response = requests.get(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}",
                        headers=github_headers
                    )
                    response.raise_for_status()
                    runs = [response.json()]
                else:
                    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs"
                    if workflow_id:
                        url += f"/workflows/{workflow_id}"
                    response = requests.get(
                        url,
                        headers=github_headers,
                        params={"per_page": 100}
                    )
                    response.raise_for_status()
                    runs = response.json()["workflow_runs"]
                # Filter runs by date if needed
                if days and not run_id:
                    cutoff_date = datetime.now() - timedelta(days=days)
                    runs = [run for run in runs if datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ") > cutoff_date]
                # Analyze runs
                total_runs = len(runs)
                if total_runs == 0:
                    return {
                        "status": "error",
                        "error": "No pipeline runs found for the specified criteria"
                    }
                successful_runs = sum(1 for run in runs if run["conclusion"] == "success")
                failed_runs = sum(1 for run in runs if run["conclusion"] == "failure")
                cancelled_runs = sum(1 for run in runs if run["conclusion"] == "cancelled")
                durations = []
                for run in runs:
                    if run["conclusion"] in ["success", "failure"]:
                        start_time = datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                        end_time = datetime.strptime(run["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
                        duration = (end_time - start_time).total_seconds() / 60
                        durations.append(duration)
                avg_duration = sum(durations) / len(durations) if durations else 0
                recommendations = []
                success_rate = (successful_runs / total_runs) * 100
                if success_rate < 80:
                    recommendations.append({
                        "type": "success_rate",
                        "priority": "high",
                        "message": f"Low success rate ({success_rate:.1f}%). Review recent failures and consider improving test coverage."
                    })
                if avg_duration > 30:
                    recommendations.append({
                        "type": "duration",
                        "priority": "medium",
                        "message": f"Long average pipeline duration ({avg_duration:.1f} minutes). Consider optimizing pipeline steps or using caching."
                    })
                recent_failures = []
                if failed_runs > 0:
                    for run in runs:
                        if run["conclusion"] == "failure":
                            try:
                                jobs_response = requests.get(
                                    run["jobs_url"],
                                    headers=github_headers
                                )
                                jobs_response.raise_for_status()
                                jobs = jobs_response.json()["jobs"]
                                for job in jobs:
                                    if job["conclusion"] == "failure":
                                        recent_failures.append({
                                            "job_name": job["name"],
                                            "failed_at": job["completed_at"]
                                        })
                            except requests.exceptions.RequestException:
                                continue
                    if recent_failures:
                        failure_patterns = {}
                        for failure in recent_failures:
                            job_name = failure["job_name"]
                            if job_name not in failure_patterns:
                                failure_patterns[job_name] = 0
                            failure_patterns[job_name] += 1
                        for job_name, count in failure_patterns.items():
                            if count >= 2:
                                recommendations.append({
                                    "type": "failure_pattern",
                                    "priority": "high",
                                    "message": f"Job '{job_name}' failed {count} times. Review and fix recurring issues."
                                })
                return {
                    "status": "success",
                    "data": {
                        "summary": {
                            "total_runs": total_runs,
                            "successful_runs": successful_runs,
                            "failed_runs": failed_runs,
                            "cancelled_runs": cancelled_runs,
                            "success_rate": f"{success_rate:.1f}%",
                            "average_duration": f"{avg_duration:.1f} minutes"
                        },
                        "recommendations": recommendations,
                        "recent_failures": recent_failures if failed_runs > 0 else []
                    }
                }
            except requests.exceptions.RequestException as e:
                return {
                    "status": "error",
                    "error": f"Failed to fetch pipeline data: {str(e)}"
                }
        except Exception:
            return {
                "status": "error",
                "error": "Pipeline analysis failed"
            } 