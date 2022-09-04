import logging
import os
import re
import shutil
from tempfile import mkdtemp

from cataloger_python_engine.lazy_coders.lazy_coders import LazyCoders


class LazyMongoose(LazyCoders):
    OUTPUT_PREFIX = './temp/lazy_mongoose/'

    RE_SCHEMA_NAME = ".*const\s+(\w+)Schema"
    RE_SCHEMA_INHERITED = ".*const\s+(\w+)Schema.*\((\w+)Schema"
    RE_ARRAY_FIELD = "\s+(\w+)\:\s+\[.*\'(\w+).*\]"
    RE_ARRAY_SCHEMA = "\s+(\w+)\:\s+\[(\w+)\]"
    RE_SCHEMA_FIELD = "\s+(\w+)\:\s+\{.*\'(\w+).*\}"
    RE_FIELD = "\s+(\w+)\:\s+\{type\:\s+(\w+).*"
    RE_SIMPLE_FIELD = "\s+(\w+)\:\s+(\w+)"
    RE_SIMPLE_FIELD_ENUM = "\s+(\w+)\:\s+\{type\:\s+(\w+).*enum.*"

    TABS = '    '
    IMPORTS = 'imports'
    BODY = 'body'

    TYPE_CONVERSION = {
        'String': 'string',
        'Date': 'Date',
        'Number': 'Number',
        'Boolean': 'boolean'
    }

    IMPORT_DOCUMENT = 'import {Document} from "mongoose";'

    WRITE_MODE = True

    LAZY_BEGIN = '// Lazy Begin'
    LAZY_END = '// Lazy End'
    LAZY_BEGIN_IMPORTS = '// Lazy Begin Imports'
    LAZY_END_IMPORTS = '// Lazy End Imports'
    LAZY_BEGIN_PROMISES = '// Lazy Begin Promises'
    LAZY_END_PROMISES = '// Lazy End Promises'
    LAZY_BEGIN_BRO = '// Lazy Begin Bro'
    LAZY_END_BRO = '// Lazy End Bro'

    END_TAGS = {
        LAZY_BEGIN_IMPORTS: LAZY_END_IMPORTS,
        LAZY_BEGIN_PROMISES: LAZY_END_PROMISES,
        LAZY_BEGIN_BRO: LAZY_END_BRO,
        LAZY_BEGIN: LAZY_END,
    }

    def __init__(self) -> None:
        super().__init__()

        # attributes
        self.__schemes_folder = None
        self.__models_folder = None
        self.__conns_folder = None

        self.__schemes = {}
        self.__models = {}

        self.__output_base_path = None

        self.schema_cap_names = {}
        self.cap_name_schemas = {}
        self.schema_classes = {}
        self.model_classes = {}

        self.interfaces = []
        self.connections = {}

    def scan_directory(self, dir_abs_path):
        # default main folders that will be edited
        self.__schemes_folder = os.path.join(dir_abs_path, 'schemas') + '/'
        self.__models_folder = os.path.join(dir_abs_path, 'models')
        self.__conns_folder = os.path.join(dir_abs_path, 'connections')

        # scanning existing schemas and models
        self.__scan_files_recursively(self.__schemes_folder, self.__schemes, '.ts', '.schema.ts')
        self.__scan_files_recursively(self.__models_folder, self.__models, '.ts', '.model.ts')

        # cleaning temporal folder
        try:
            shutil.rmtree(self.OUTPUT_PREFIX, True)
            os.makedirs(self.OUTPUT_PREFIX)
            self.__output_base_path = mkdtemp(dir=self.OUTPUT_PREFIX)
        except FileExistsError as fee:
            pass

        # analyzing schemas to cover possible dependencies between models
        for model_name in self.__schemes.keys():
            self.__analyze_schema(model_name)
        # model generation
        for model_name in self.__schemes.keys():
            self.interfaces = []
            gen_model = self.__generate_model(model_name)
            self.__write_new_model(model_name, gen_model)
        # connections generation
        # for conn_name in self.connections:
        #     self.connections[conn_name].sort()
        #     self.write_connection(conn_name)
        #     self.write_configurations(subdir_folder)

        logging.info(dir_abs_path)
        logging.info(self.__output_base_path)

    def __create_emtpy_model_file(self, dir_path, file_name):
        file_path = os.path.join(dir_path, file_name)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        if not os.path.exists(file_path):
            with open(file_path, 'w') as new_model_file:
                new_model_file.write(self.LAZY_BEGIN_IMPORTS + '\n')
                new_model_file.write(self.LAZY_END_IMPORTS + '\n')
                new_model_file.write('\n')
                new_model_file.write(self.LAZY_BEGIN + '\n')
                new_model_file.write(self.LAZY_END + '\n')

        return file_path

    def __write_new_model(self, model_name, gen_model):
        # obtenemos la ruta del modelo
        sub_folder = self.__scheme_sub_folder(model_name)
        folder = os.path.join(self.__output_base_path, sub_folder)
        try:
            os.makedirs(folder)
        except FileExistsError as fee:
            pass
        self.__save_model_in_connections(model_name)

        # escribimos el nuevo fichero de modelo
        new_file = os.path.join(folder, f'{model_name}.model.ts')
        original_folder = os.path.join(self.__models_folder, sub_folder)

        if self.WRITE_MODE:
            original_file = self.__create_emtpy_model_file(original_folder, os.path.basename(new_file))
        else:
            original_file = self.__create_emtpy_model_file(folder, 'empty.model.ts')

        lazy_blocks = [
            {
                'tag': self.LAZY_BEGIN_IMPORTS,
                'lines': gen_model[self.IMPORTS]
            },
            {
                'tag': self.LAZY_BEGIN,
                'lines': gen_model[self.BODY]
            }
        ]
        self.__lazy_writer(original_file, new_file, lazy_blocks, model_name)

    def __generate_model(self, model_name):
        gen_model = {
            self.IMPORTS: [],
            self.BODY: []
        }
        with open(self.__schemes[model_name], 'r') as schema_file:
            schema_def = None
            for line in schema_file:
                m_schema = re.match(self.RE_SCHEMA_NAME, line)
                if m_schema:
                    # flag
                    schema_def = line
                    # TODO get the class name from the cache
                    schema_cap_name = f'{m_schema.group(1)[0].upper()}{m_schema.group(1)[1:]}'

                    # check possible schema inheritance
                    m_schema_inherited = re.match(self.RE_SCHEMA_INHERITED, line)
                    if m_schema_inherited:
                        inherit = m_schema_inherited.group(2)
                        gen_model[self.BODY].append(f'export interface I{schema_cap_name} extends I{inherit} ' + '{')
                        self.__convert_type(model_name, gen_model, inherit)
                    else:
                        gen_model[self.BODY].append(f'export interface I{schema_cap_name} extends Document ' + '{')
                        # vemos si hay que meter el import
                        if self.IMPORT_DOCUMENT not in gen_model[self.IMPORTS]:
                            gen_model[self.IMPORTS].append(self.IMPORT_DOCUMENT)
                    self.interfaces.append(f'I{schema_cap_name}')

                    continue

                if schema_def:
                    m_array = re.match(self.RE_ARRAY_FIELD, line)
                    m_array_schema = re.match(self.RE_ARRAY_SCHEMA, line)

                    m_field = re.match(self.RE_FIELD, line)
                    m_schema_field = re.match(self.RE_SCHEMA_FIELD, line)
                    m_simple_field = re.match(self.RE_SIMPLE_FIELD, line)
                    m_simple_field_enum = re.match(self.RE_SIMPLE_FIELD_ENUM, line)

                    # vemos que tipo de fie§ld es
                    m_field = m_schema_field if m_schema_field else m_field
                    m_field = m_simple_field if not m_field else m_field
                    m_field = m_simple_field_enum if m_simple_field_enum else m_field

                    if m_array:  # es un array
                        # logging.info(f'{m_array.group(1)}  -> {m_array.group(2)}')
                        field_type = self.__convert_type(model_name, gen_model, m_array.group(2), True)
                        gen_model[self.BODY].append(f'{self.TABS}{m_array.group(1)}: {field_type};')
                    elif m_array_schema:
                        field_type = self.__convert_type(model_name, gen_model, m_array_schema.group(2), True)
                        gen_model[self.BODY].append(f'{self.TABS}{m_array_schema.group(1)}: {field_type};')
                    elif m_field:
                        # logging.info(f'{m_field.group(1)}  -> {m_field.group(2)}')
                        field_type = self.__convert_type(model_name, gen_model, m_field.group(2))
                        gen_model[self.BODY].append(f'{self.TABS}{m_field.group(1)}: {field_type};')
                    else:
                        schema_def = None
                        gen_model[self.BODY].append('}\n')

        if schema_def:
            schema_def = None
            gen_model[self.BODY].append('}\n')

        for gen_model_line in gen_model[self.BODY]:
            logging.info(gen_model_line)

        return gen_model

    def __analyze_schema(self, model_name):
        with open(self.__schema_path(model_name), 'r') as schema_file:
            for line in schema_file:
                m_schema = re.match(self.RE_SCHEMA_NAME, line)
                if m_schema:
                    # generate class name
                    schema_cap_name = f'{m_schema.group(1)[0].upper()}{m_schema.group(1)[1:]}'

                    # save class references if it is the main one
                    if model_name.replace('-', '').lower() == m_schema.group(1).lower():
                        self.schema_cap_names[model_name] = schema_cap_name
                        self.cap_name_schemas[schema_cap_name] = model_name
                        self.schema_classes[model_name] = f'{schema_cap_name}Schema'
                        self.model_classes[model_name] = f'I{schema_cap_name}'

    def __check_extended_model(self, model_name, line):
        try:
            extended_model = f'{self.model_classes[model_name]}Model'
            if extended_model in line:
                self.model_classes[model_name] = extended_model
        except KeyError as ke:
            logging.warning(f'Modelo {model_name} no encontrado en el diccionario de modelos')

    def __lazy_writer(self, original_file, new_file, lazy_blocks, model_name=None):
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
                        elif line.strip() == self.END_TAGS[lazy_block['tag']]:
                            write_allowed = False
                    # escribimos las partes no automatizadas
                    if not write_allowed:
                        new_lazy_file.write(line)

                    if model_name:
                        self.__check_extended_model(model_name, line)

        # escribimos el resultado
        if self.WRITE_MODE:
            dst_folder = os.path.join(os.path.abspath(original_file))
            try:
                os.makedirs(dst_folder)
            except FileExistsError as fee:
                pass
            dst_file = os.path.join(original_file)
            shutil.copyfile(new_file, dst_file)

    def __save_model_in_connections(self, model_name):
        conn_name = self.__connection_name(model_name)
        if conn_name:
            if conn_name not in self.connections.keys():
                self.connections[conn_name] = []
            self.connections[conn_name].append(model_name)

    def __type_model_name(self, type):
        if type.lower() in self.__schemes.keys():
            return type.lower()
        else:
            return self.cap_name_schemas[type]

    def __scheme_sub_folder(self, model_name):
        full_path = self.__schema_path(model_name.lower())
        basename = os.path.basename(full_path)

        result = full_path.replace(self.__schemes_folder, '')
        result = result.replace(basename, '')
        return result

    def __connection_name(self, model_name):
        return self.__scheme_sub_folder(model_name).replace('/', '')

    def __convert_type(self, current_model, gen_model, type, is_array=False):
        if type in self.TYPE_CONVERSION.keys():
            result = self.TYPE_CONVERSION[type]
        else:
            result = f'I{type[0].upper()}{type[1:]}'
            result = result.replace('Schema', '')
            # añadimos el import de la interfaz
            if result not in self.interfaces:
                self.interfaces.append(result)
                current_conn_name = self.__connection_name(current_model)
                model_name = self.__type_model_name(type)
                conn_name = self.__connection_name(model_name)
                if conn_name:
                    if conn_name != current_conn_name:
                        gen_model[self.IMPORTS].append(
                            f'import {"{" + result + "}"} from "../{conn_name}/{model_name}.model";')

                    else:
                        gen_model[self.IMPORTS].append(f'import {"{" + result + "}"} from "./{model_name}.model";')
                else:
                    gen_model[self.IMPORTS].append(f'import {"{" + result + "}"} from "../{model_name}.model";')

        if is_array:
            result = f'[{result}]'

        return result

    def __schema_path(self, model_name):
        return self.__schemes[model_name]

    def __scan_files_recursively(self, folder, cache, ext, suffix):
        for root, dirs, files in os.walk(folder, topdown=True):
            for f in files:
                if f.endswith(ext):
                    cache[os.path.basename(f).replace(suffix, '')] = os.path.join(root, f)
