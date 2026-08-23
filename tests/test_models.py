import unittest

from deployment_agent.models import ProjectSpec, ServiceSpec

class DeploymentModelTests(unittest.TestCase):
    def test_service_uses_independent_script_dictionary(self):
        first_service = ServiceSpec(
            name="frontend",
            root=".",
            framework="next.js",
            version="16.0.0",
            package_manager="npm",
            install_command="npm ci",
            build_command="npm run build",
            start_command="npm run start",
        )
        second_service = ServiceSpec(
            name="backend",
            root="api",
            framework="node",
            version="22",
            package_manager="npm",
            install_command="npm ci",
            build_command="npm run build",
            start_command="npm run start",
        )

        first_service.scripts["build"] = "next build"

        self.assertEqual(
            first_service.scripts,
            {"build": "next build"},
        )
        self.assertEqual(second_service.scripts, {})
        self.assertEqual(first_service.port, 3000)

    def test_project_can_be_converted_to_dictionary(self):
        service = ServiceSpec(
            name="shop",
            root=".",
            framework="next.js",
            version="16.0.0",
            package_manager="npm",
            install_command="npm ci",
            build_command="npm run build",
            start_command="npm run start",
            scripts={
                "build": "next build",
                "start": "next start",
            },
        )

        project = ProjectSpec(
            name="online-shop",
            source_path="/projects/online-shop",
            services=[service],
            warnings=["Environment variables require review"],

        )
        result = project.to_dict()

        self.assertEqual(result["name"], "online-shop")
        self.assertEqual(
            result["services"][0]["framework"],
            "next.js",
        )
        self.assertEqual(
            result["services"][0]["scripts"]["build"],
            "next build",
        )
        self.assertEqual(
            result["warnings"],
            ["Environment variables require review"],
        )

if __name__ == "__main__":
    unittest.main()