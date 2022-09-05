import logging
import os
import shutil
from abc import ABC, abstractmethod


class LazyCoders(ABC):

    def __init__(self) -> None:
        super().__init__()

    def _lazy_writer(self, original_file, new_file, lazy_blocks, extra=None):
        with open(new_file, 'w') as new_lazy_file:
            with open(original_file) as model_file:
                write_allowed = False
                for line in model_file:
                    logging.info(line)
                    for lazy_block in lazy_blocks:
                        if line.strip() == lazy_block['tag']:
                            write_allowed = True
                            tabs = line[:line.index('/')]
                            new_lazy_file.write(tabs + lazy_block['tag'] + '\n')
                            for lazy_block_line in lazy_block['lines']:
                                new_lazy_file.write(tabs + lazy_block_line + '\n')
                        elif line.strip() == self._end_tags()[lazy_block['tag']]:
                            write_allowed = False
                    # escribimos las partes no automatizadas
                    if not write_allowed:
                        new_lazy_file.write(line)

                    if extra:
                        self._line_hook(line, extra)

        # escribimos el resultado
        if self._write_mode():
            dst_folder = os.path.join(os.path.abspath(original_file))
            try:
                os.makedirs(dst_folder)
            except FileExistsError as fee:
                pass
            dst_file = os.path.join(original_file)
            shutil.copyfile(new_file, dst_file)

    @abstractmethod
    def _end_tags(self):
        pass

    @abstractmethod
    def _write_mode(self):
        pass

    @abstractmethod
    def _line_hook(self, line, extra=None):
        pass
