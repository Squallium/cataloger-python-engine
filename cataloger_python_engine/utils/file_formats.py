import logging
import os
import shutil


class FileFormats:
    IGNORED_FOLDERS = ('node_modules',)
    SKIP_EXTENSIONS = ('.DS_Store', '.png', '.jpg', '.jpeg', '.ico', '.gif')

    def __init__(self) -> None:
        super().__init__()

    def convert_crlf_to_lf(self, project_path):
        for root, dirs, files in os.walk(project_path, topdown=True):
            f: str
            filtered_files = [os.path.join(root, f) for f in files if self.is_valid(root, f)]

            for file_path in filtered_files:
                logging.info(os.path.join(root, file_path))

                shutil.copyfile(file_path, file_path + '.temp')
                with open(file_path + '.temp', 'r') as infile, \
                        open(file_path, 'w', newline='\n') as outfile:
                    outfile.writelines(infile.readlines())
                os.remove(file_path + '.temp')

    def is_valid(self, folder, file):
        return not any(str_ in folder for str_ in self.IGNORED_FOLDERS) and not file.endswith(self.SKIP_EXTENSIONS)