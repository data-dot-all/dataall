import logging
import yaml
import os
from jinja2 import Template

logger = logging.getLogger()


class MissingConfigArgument(Exception):
    def __init__(self, arg_name):
        super().__init__()
        self.message = f'Missing Config Argument {arg_name}. Make sure you have passed {arg_name} in args parameter of the config object.'

    def __str__(self):
        return self.message


class AthenaConfigReader:
    """Class to read configuration file corresponds to an Athena job.
    ConfigReader(path=f"/tmp/{args.get("CONFIGPATH")h}")
    Parameters
        path: the file path.
        config: configuration in string, instead of file.
        variables: The variables to be used for templating.
    """

    def __init__(self, config_path='config.yaml', config: str = None, variables={}):
        self.config_path = config_path
        self.config = config
        self.steps = []
        self.queries = []
        self.variables = variables
        self.job_dir = 'customcode/athena/athena_jobs'
        self.steps_definition = self.get_steps_definition()

    # Methods
    def _get_file(self, path):
        """Read file from local"""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
                return '\n'.join(lines)
        except Exception as e:
            raise Exception(
                'FileNotFound', message=f'could not find file at path {path} {e}'
            )

    def _parse_variables(self, config):
        variable_file = config.get('variables', {}).get('file')

        if variable_file:
            try:
                variable_lines = self._get_file(f'{variable_file}')
                template = Template(variable_lines)
                rendered = template.render()

                self.variables = yaml.safe_load(rendered)
            except Exception as e:

                logging.error('Could not parse variable files ')
                raise e

    def _parse_query(self, query):
        if query.get('type') == 'sql':
            if query.get('config').get('file'):
                list_files = query.get('config').get('file').split(',')

                is_first = True
                for file_path in list_files:
                    path = os.path.realpath(
                        os.path.join(os.path.dirname(__file__), '..', '..', file_path)
                    )
                    try:
                        sql_lines = self._get_file(os.path.abspath(path))
                        template = Template(sql_lines)
                        query_str = template.render(self.variables)

                        if is_first:
                            query_string = f'{query_str}'
                            is_first = False
                        else:
                            query_string = query_string + ';' + query_str
                    except Exception as e:
                        logging.error('Could not parse variable files ')
                        raise e

        else:  # Prepared statement
            # Variables should be a list ["$$.execution.id", "$.isFirst"]
            try:
                variables_str = ','.join(self.variables)
                prepared_statement = query.get('config').get('prepared_statement')
                sql_unrendered = 'EXECUTE {} USING {{}}'.format(prepared_statement)
                query_string = f"States.Format('{sql_unrendered}',{variables_str})"

            except Exception as e:
                logging.error('Problem loading prepared statement')
                raise e

        return query_string

    def get_steps_definition(self):
        config = {}
        self.steps = []
        self.queries = []

        try:
            print(self.config_path)
            f = open(self.config_path, 'r')
            template = Template('\n'.join(f.readlines()))

            # 1. get athena config file
            rendered = template.render(self.variables)
            config = yaml.safe_load(rendered)
            self.steps = config.get('steps')

            # 2. build steps with sql statements

            for step in config.get('steps', []):
                queries_rendered = []
                for job in step.get('jobs', []):
                    query_name = job.get('name')
                    logging.info(f'Query task: {query_name}')
                    query_rendered = self._parse_query(job)
                    queries_rendered.append(query_rendered)
                self.queries.append(queries_rendered)

        except FileNotFoundError:
            logging.error(f'File {self.config_path} is not found')
            raise
        except Exception:
            logging.error(
                f'Can not parse [{self.config_path}] as configuration file. Check the configuration file format.'
            )
            raise

        return self.queries, self.steps
