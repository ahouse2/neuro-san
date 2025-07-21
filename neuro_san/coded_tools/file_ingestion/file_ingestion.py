import os
import shutil
from neuro_san.interfaces.coded_tool import CodedTool

class FileIngestionTool(CodedTool):
    def upload(self, path: str):
        """
        Uploads a file or directory to the system.

        :param path: The path to the file or directory to upload.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"The path '{path}' does not exist.")

        # For the purpose of this example, we will just print the path.
        # In a real implementation, this would involve moving the file to a
        # storage system, such as S3 or a local file store.
        print(f"Uploading '{path}' to the system.")
