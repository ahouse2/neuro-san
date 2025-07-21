import os
from neuro_san.interfaces.coded_tool import CodedTool

class MetadataExtractorTool(CodedTool):
    def extract(self, path: str):
        """
        Extracts metadata from a file.

        :param path: The path to the file.
        :return: A dictionary of metadata.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"The path '{path}' does not exist.")

        # For the purpose of this example, we will just return some basic
        # metadata. In a real implementation, this would involve using a
        # library like 'hachoir' to extract detailed metadata.
        return {
            "size": os.path.getsize(path),
            "last_modified": os.path.getmtime(path),
        }
