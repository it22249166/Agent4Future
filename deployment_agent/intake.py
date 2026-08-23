from __future__ import annotations

import json
from pathlib import Path

from .models import ProjectSpec, ServiceSpec

class IntakeAgent:
    def analyze(
            self,
            source_path: Path | str,
    ) -> ProjectSpec:
        root = Path(source_path).resolve()

        if not root.is_dir():
            raise ValueError(
                f"Project directory not found: {root}"
            )

        package = self._read_package_json(root)
        scripts = package.get("scripts") or {}

        if not isinstance(scripts, dict):
            raise ValueError(
                "package.json scripts must be an object"
            )

        dependencies = package.get("dependencies") or {}
        development_dependencies = (
            package.get("devDependencies") or {}
        )

        if not isinstance(dependencies, dict):
            raise ValueError(
                "package.json dependencies must be an object"
            )

        if not isinstance(development_dependencies, dict):
            raise ValueError(
                "package.json devDependencies must be an object"
            )

        all_dependencies = {
            **dependencies,
            **development_dependencies,
        }

        framework, version = self._detect_framework(
            all_dependencies
        )

        (
            package_manager,
            install_command,
            has_lockfile
        ) = self._detect_package_manager(root)

        warnings: list[str] = []

        if not has_lockfile:
            warnings.append(
                "No lockfile found; dependency installation "
                "may not be reproducible"
            )

        if "build" not in scripts:
            warnings.append(
                "Build script is missing"
            )

        if "start" not in scripts:
            warnings.append(
                "Start script is missing"
            )

        project_name = str(
            package.get("name") or root.name
        )

        service = ServiceSpec(
            name=project_name,
            root=".",
            framework=framework,
            version=version,
            package_manager=package_manager,
            install_command=install_command,
            build_command=(
                f"{package_manager} run build"
                if "build" in scripts
                else ""
            ),
            start_command=(
                f"{package_manager} run start"
                if "start" in scripts
                else ""
            ),
            scripts={
                str(name): str(command)
                for name, command in scripts.items()
            },
        )

        return ProjectSpec(
            name=project_name,
            source_path=str(root),
            services=[service],
            warnings=warnings,
        )

    @staticmethod
    def _read_package_json(root: Path) -> dict:
        package_path = root / "package.json"

        if not package_path.is_file():
            raise ValueError(
                f"package.json not found: {package_path}"
            ) 
        try:
            package = json.loads(
                package_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid package.json: {error}"
            ) from error

        if not isinstance(package, dict):
            raise ValueError(
                "package.json root must be an object"
            )

        return package

    @staticmethod
    def _detect_framework(
        dependencies: dict,
    ) -> tuple[str, str]:
        candidates = (
            ("next", "nextjs"),
            ("react","react"),
            ("express","express"),
        )

        for package_name, framework_name in candidates:
            if package_name in dependencies:
                return(
                    framework_name,
                    str(dependencies[package_name]),
                )
        return "node", ""

    @staticmethod
    def _detect_package_manager(
        root:Path,
    ) -> tuple[str, str, bool]:
        if(root / "pnpm-lock.yml").is_file():
            return(
                "pnpm",
                "pnpm install --frozen-lockfile",
                True,
            )

        if (root / "yarn.lock").is_file():
            return (
                "yarn",
                "yarn install --frozen-lockfile",
                True,
            )

        if (root / "package-lock.json").is_file():
            return (
                "npm",
                "npm ci",
                True,
            )

        return "npm", "npm install", False
        