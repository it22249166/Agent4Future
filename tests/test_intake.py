import json
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from deployment_agent.intake import IntakeAgent

class IntakeAgentTests(unittest.TestCase):

    def setUp(self):
        self.temp_directory = TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.agent = IntakeAgent()

    def tearDown(self):
        self.temp_directory.cleanup()

    def write_package(self, package: dict) -> None:
        package_path = self.root / "package.json"
        package_path.write_text(
            json.dumps(package),
            encoding="utf-8",
        )

    def test_detects_nextjs_project_using_npm(self):
        self.write_package(
            {
                "name": "shop-app",
                "scripts": {
                    "build": "next build",
                    "start": "next start",
                },
                "dependencies": {
                    "next": "^16.0.0",
                    "react": "^19.0.0",
                },
            }
        )

        (self.root / "package-lock.json").write_text(
            "{}",
            encoding= "utf-8",
        )

        project = self.agent.analyze(self.root)
        service = project.services[0]

        self.assertEqual(project.name, "shop-app")
        self.assertEqual(service.framework, "nextjs")
        self.assertEqual(service.version, "^16.0.0")
        self.assertEqual(service.package_manager, "npm")
        self.assertEqual(service.install_command, "npm ci")
        self.assertEqual(
            service.build_command,
            "npm run build"
        )
        self.assertEqual(project.warnings, [])

    def test_missing_package_json_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "package.json not found",
        ):
            self.agent.analyze(self.root)

    def test_invalid_package_is_rejected(self):
        (self.root / "package.json").write_text(
            "{invalid-json}",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            ValueError,
            "Invalid package.json",
        ):
            self.agent.analyze(self.root)

    def test_missing_lockfile_and_scripts_create_warnings(self):
        self.write_package(
            {
                "name": "api-service",
                "dependencies": {
                    "express": "^5.0.0",
                },
            }
        )

        project = self.agent.analyze(self.root)
        service = project.services[0]

        self.assertEqual(service.framework, "express")
        self.assertEqual(service.install_command, "npm install")
        self.assertIn(
            "No lockfile found; dependency installation "
            "may not be reproducible",
            project.warnings,
        )
        self.assertIn(
            "Build script is missing",
            project.warnings,
        )
        self.assertIn(
            "Start script is missing",
            project.warnings,
        )

if __name__ == "__main__":
    unittest.main()