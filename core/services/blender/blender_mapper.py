import logging
import os

import docker

logger = logging.getLogger(__name__)


class BlenderImageMapper:
    """
    Runs a Blender rendering task inside a Docker container to generate a 3D mockup.

    Uses a custom `.blend` template, a user-provided image, and a Python script to render
    an output image inside the 'blender_runner' container using the Docker SDK.
    """
    def __init__(self, image_path: str, model_path: str, output_path: str) -> None:
        """
        Initializes the BlenderImageMapper with input/output paths and prepares Docker client.

        Args:
            image_path (str): Relative path to the input image that will be applied to the 3D model.
            model_path (str): Relative path to the Blender `.blend` template file.
            output_path (str): Relative path where the rendered image will be saved.
        """
        base_mount = "/app"
        self.blend_file = os.path.join(base_mount, model_path)
        self.image_path = os.path.join(base_mount, image_path)
        self.output_path = os.path.join(base_mount, output_path)
        self.script_path = os.path.join(base_mount, "core/services/blender/blender_script.py")

        self.client = docker.from_env()

    def run(self) -> None:
        """
        Executes the Blender rendering process inside the Docker container.

        This method:
          - Mounts the required paths inside the container.
          - Runs Blender in background mode with a Python script and the provided assets.
          - Captures and logs both stdout and stderr from the container process.
          - Raises an exception if the Blender process fails or the container is not found.
        """
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        command = [
            "blender",
            "-b", self.blend_file,
            "-P", self.script_path,
            "--",
            self.blend_file,
            self.image_path,
            self.output_path
        ]

        try:
            container = self.client.containers.get("blender_runner")
            result = container.exec_run(
                cmd=command,
                stdout=True,
                stderr=True,
                demux=True
            )
            stdout, stderr = result.output
            if stdout:
                logger.info("Blender stdout:\n%s", stdout.decode())
            if stderr:
                logger.info("Blender stderr:\n%s", stderr.decode())

            if result.exit_code != 0:
                raise RuntimeError(f"Blender command failed with exit code {result.exit_code}")

        except docker.errors.NotFound:
            logger.error("Container 'blender_runner' not found")
            raise
        except Exception as e:
            logger.error(f"Blender command failed: {e}")
            raise
