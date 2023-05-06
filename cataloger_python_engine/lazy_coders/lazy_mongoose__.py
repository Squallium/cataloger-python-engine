import logging
import os
import re
import shutil

from cataloger_python_engine.lazy_coders.lazy_coders import LazyCoders


class LazyMongoose(LazyCoders):
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

    TABS = '    '
    IMPORTS = 'imports'
    BODY = 'body'

    IMPORT_DOCUMENT = 'import {Document} from "mongoose";'

    PERSONAL_PATH = '/Users/borja.refoyo/Personal'
    DEV_OPS_PATH = '/Users/borja.refoyo/DevOps'
    FRONTEND_PROJECT_PATH = os.path.join(PERSONAL_PATH, 'metronic')

    PROJECTS = {
        'vine': os.path.join(PERSONAL_PATH, 'vine-microservice'),
        'template': os.path.join(PERSONAL_PATH, 'template-microservice'),
        'lego': os.path.join(PERSONAL_PATH, 'lego-microservice'),
        'cortex': os.path.join(PERSONAL_PATH, 'cortex-microservice'),
        'comic': os.path.join(PERSONAL_PATH, 'comic-microservice'),
        'user': os.path.join(PERSONAL_PATH, 'user-microservice'),
        'abs': os.path.join(DEV_OPS_PATH, 'abs-backend'),
        'devops-admin': os.path.join(DEV_OPS_PATH, 'devops-admin'),
    }

    RE_SCHEMA_NAME = ".*const\s+(\w+)Schema"
    RE_SCHEMA_INHERITED = ".*const\s+(\w+)Schema.*\((\w+)Schema"
    RE_ARRAY_FIELD = "\s+(\w+)\:\s+\[.*\'(\w+).*\]"
    RE_ARRAY_SCHEMA = "\s+(\w+)\:\s+\[(\w+)\]"
    RE_SCHEMA_FIELD = "\s+(\w+)\:\s+\{.*\'(\w+).*\}"
    RE_FIELD = "\s+(\w+)\:\s+\{type\:\s+(\w+).*"
    RE_SIMPLE_FIELD = "\s+(\w+)\:\s+(\w+)"
    RE_SIMPLE_FIELD_ENUM = "\s+(\w+)\:\s+\{type\:\s+(\w+).*enum.*"

    OUTPUT_BASE_PATH = 'temp/lazy_mongoose/'

    def __init__(self, params) -> None:
        self.project, self.module = params

        self.schemes_folder = None
        self.models_folder = None
        self.conns_folder = None

        self.dep_schemes_folder = None
        self.dep_models_folder = None

        self.schemes = {}
        self.models = {}
        self.interfaces = []

        self.dep_schemes = {}
        self.dep_models = {}

        self.schema_cap_names = {}
        self.cap_name_schemas = {}
        self.schema_classes = {}
        self.model_classes = {}
        self.connections = {}

    def run_job(self):
        # self.scan_folder('base')
        # self.scan_folder('', 'base')
        self.scan_folder('')

    def scan_folder(self, subdir_folder, dep=None):
        core_folder = os.path.join(self.PROJECTS[self.project], subdir_folder)
        self.schemes_folder = os.path.join(core_folder, 'schemas') + '/'
        self.models_folder = os.path.join(core_folder, 'models')
        self.conns_folder = os.path.join(core_folder, 'connections')

        for root, dirs, files in os.walk(self.schemes_folder, topdown=True):
            for f in files:
                if f.endswith('.ts'):
                    self.schemes[os.path.basename(f).replace('.schema.ts', '')] = os.path.join(root, f)

        for root, dirs, files in os.walk(self.models_folder, topdown=True):
            for f in files:
                if f.endswith('.ts'):
                    self.models[os.path.basename(f).replace('.model.ts', '')] = os.path.join(root, f)

        if dep:
            self.dep_schemes_folder = os.path.join(core_folder, dep, 'schemas') + '/'
            for root, dirs, files in os.walk(self.dep_schemes_folder, topdown=True):
                for f in files:
                    if f.endswith('.ts'):
                        self.dep_schemes[os.path.basename(f).replace('.schema.ts', '')] = os.path.join(root, f)

            self.dep_models_folder = os.path.join(core_folder, dep, 'models')
            for root, dirs, files in os.walk(self.dep_models_folder, topdown=True):
                for f in files:
                    if f.endswith('.ts'):
                        self.dep_models[os.path.basename(f).replace('.model.ts', '')] = os.path.join(root, f)

        # limpiamos la carpeta temporal
        try:
            shutil.rmtree(self.OUTPUT_BASE_PATH, True)
            os.makedirs(self.OUTPUT_BASE_PATH)
        except FileExistsError as fee:
            pass

        for model_name in self.schemes.keys():
            self.analyze_model(model_name)
        for model_name in self.dep_schemes.keys():
            self.analyze_model(model_name)
        for model_name in self.schemes.keys():
            self.interfaces = []
            gen_model = self.generate_model(model_name)
            self.write_new_model(model_name, gen_model)
        for conn_name in self.connections:
            self.connections[conn_name].sort()
            self.write_connection(conn_name)
            self.write_configurations(subdir_folder)
        # model_name = 'module'
        # gen_model = self.generate_model(model_name)
        # self.write_new_model(model_name, gen_model)
        # self.write_connection(model_name)

    def write_configurations(self, subdir_folder):
        new_file = os.path.join(self.OUTPUT_BASE_PATH, f'app.ts')
        original_file = os.path.join(self.PROJECTS[self.project], subdir_folder, f'app.ts')

        lines_import = []
        lines_promises = []
        lines_bro = []

        for conn_name in self.connections.keys():
            conn_class = f'{conn_name[0].upper()}{conn_name[1:]}'
            # conn_path = os.path.join('.', subdir_folder, f'connections/{conn_name}.conn')
            conn_path = os.path.join('', f'connections/{conn_name}.conn')

            lines_import.append(f'import {"{" + conn_class + "Conn}"} from "{conn_path}";')
            lines_promises.append(f'{conn_class}Conn,')
            for model_name in self.connections[conn_name]:
                schema_cap_name = self.schema_cap_names[model_name]
                lines_bro.append(f'{conn_class}Conn.model(\'{schema_cap_name}\'),')

        lazy_blocks = [
            {
                'tag': self.LAZY_BEGIN_IMPORTS,
                'lines': lines_import
            },
            {
                'tag': self.LAZY_BEGIN_PROMISES,
                'lines': lines_promises
            },
            {
                'tag': self.LAZY_BEGIN_BRO,
                'lines': lines_bro
            }
        ]
        self.__lazy_writer(original_file, new_file, lazy_blocks)

    def write_connection(self, conn_name):
        new_file = os.path.join(self.OUTPUT_BASE_PATH, f'{conn_name}.conn.ts')
        original_file = os.path.join(self.conns_folder, f'{conn_name}.conn.ts')

        lines_import = []
        lines_exports = []
        for model_name in self.connections[conn_name]:
            schema_cap_name = self.schema_cap_names[model_name]
            schema_class = self.schema_classes[model_name]
            model_class = self.model_classes[model_name]
            lines_import.append(f'import {"{" + schema_class + "}"} from "../schemas/{conn_name}/{model_name}.schema";')
            lines_import.append(f'import {"{" + model_class + "}"} from "../models/{conn_name}/{model_name}.model";')

            lines_exports.append(
                f'export const {schema_cap_name}: Model<{model_class}> = {conn_name.capitalize()}Conn.model<{model_class}>(\'{schema_cap_name}\', {schema_class});')

        lazy_blocks = [
            {
                'tag': self.LAZY_BEGIN_IMPORTS,
                'lines': lines_import
            },
            {
                'tag': self.LAZY_BEGIN,
                'lines': lines_exports
            }
        ]
        self.__lazy_writer(original_file, new_file, lazy_blocks)

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

    def write_new_model(self, model_name, gen_model):
        # obtenemos la ruta del modelo
        sub_folder = self.__scheme_sub_folder(model_name)
        folder = os.path.join(self.OUTPUT_BASE_PATH, sub_folder)
        try:
            os.makedirs(folder)
        except FileExistsError as fee:
            pass
        self.__save_model_in_connections(model_name)

        # escribimos el nuevo fichero de modelo
        new_file = os.path.join(folder, f'{model_name}.model.ts')
        original_folder = os.path.join(self.models_folder, sub_folder)
        original_file = os.path.join(original_folder, os.path.basename(new_file))

        if not os.path.exists(original_file):
            with open(original_file, 'w') as new_model_file:
                new_model_file.write(self.LAZY_BEGIN_IMPORTS + '\n')
                new_model_file.write(self.LAZY_END_IMPORTS + '\n')
                new_model_file.write('\n')
                new_model_file.write(self.LAZY_BEGIN + '\n')
                new_model_file.write(self.LAZY_END + '\n')

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

    def analyze_model(self, model_name):
        with open(self.__schemes(model_name), 'r') as schema_file:
            for line in schema_file:
                m_schema = re.match(self.RE_SCHEMA_NAME, line)
                if m_schema:
                    # construimos el nombre de la clase
                    schema_cap_name = f'{m_schema.group(1)[0].upper()}{m_schema.group(1)[1:]}'

                    # almacenamos el nombre de la clase si es la principal
                    if model_name.replace('-', '').lower() == m_schema.group(1).lower():
                        self.schema_cap_names[model_name] = schema_cap_name
                        self.cap_name_schemas[schema_cap_name] = model_name
                        self.schema_classes[model_name] = f'{schema_cap_name}Schema'
                        self.model_classes[model_name] = f'I{schema_cap_name}'

    def __schemes(self, model_name):
        if model_name in self.dep_schemes.keys():
            return self.dep_schemes[model_name]
        else:
            return self.schemes[model_name]

    def generate_model(self, model_name):
        gen_model = {
            self.IMPORTS: [],
            self.BODY: []
        }
        with open(self.schemes[model_name], 'r') as schema_file:
            schema_def = None
            for line in schema_file:
                m_schema = re.match(self.RE_SCHEMA_NAME, line)
                if m_schema:
                    # flag
                    schema_def = line
                    # construimos el nombre de la clase
                    schema_cap_name = f'{m_schema.group(1)[0].upper()}{m_schema.group(1)[1:]}'

                    # generamos el import
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

                    # # almacenamos el nombre de la clase si es la principal
                    # if model_name.replace('-', '').lower() == m_schema.group(1).lower():
                    #     self.schema_cap_names[model_name] = schema_cap_name
                    #     self.cap_name_schemas[schema_cap_name] = model_name
                    #     self.schema_classes[model_name] = f'{schema_cap_name}Schema'
                    #     self.model_classes[model_name] = f'I{schema_cap_name}'
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

    TYPE_CONVERSION = {
        'String': 'string',
        'Date': 'Date',
        'Number': 'Number',
        'Boolean': 'boolean'
    }

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
                        if self.__is_dep_model(model_name):
                            gen_model[self.IMPORTS].append(f'import {"{" + result + "}"} from "../../base/models/{model_name}.model";')
                        else:
                            gen_model[self.IMPORTS].append(f'import {"{" + result + "}"} from "./{model_name}.model";')
                else:
                    if self.__is_dep_model(model_name):
                        gen_model[self.IMPORTS].append(f'import {"{" + result + "}"} from "../../base/models/{model_name}.model";')
                    else:
                        gen_model[self.IMPORTS].append(f'import {"{" + result + "}"} from "../{model_name}.model";')

        if is_array:
            result = f'[{result}]'

        return result

    def __is_dep_model(self, model_name):
        return model_name.lower() in self.dep_models.keys()

    def __type_model_name(self, type):
        if type.lower() in self.schemes.keys():
            return type.lower()
        else:
            return self.cap_name_schemas[type]

    def __scheme_sub_folder(self, model_name):
        full_path = self.__schemes(model_name.lower())
        basename = os.path.basename(full_path)

        result = full_path.replace(self.schemes_folder, '')
        if self.dep_schemes_folder:
            result = result.replace(self.dep_schemes_folder, '')
        result = result.replace(basename, '')
        return result

    def __connection_name(self, model_name):
        return self.__scheme_sub_folder(model_name).replace('/', '')

    def __check_extended_model(self, model_name, line):
        try:
            extended_model = f'{self.model_classes[model_name]}Model'
            if extended_model in line:
                self.model_classes[model_name] = extended_model
        except KeyError as ke:
            logging.warning(f'Modelo {model_name} no encontrado en el diccionario de modelos')

    def __save_model_in_connections(self, model_name):
        conn_name = self.__connection_name(model_name)
        if conn_name:
            if conn_name not in self.connections.keys():
                self.connections[conn_name] = []
            self.connections[conn_name].append(model_name)
