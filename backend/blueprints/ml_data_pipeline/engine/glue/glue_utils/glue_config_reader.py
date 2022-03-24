import logging
import os

import boto3
import yaml

from jinja2 import Template
from engine.glue.handlers import StepInterface

logger = logging.getLogger()


class MissingConfigArgument(Exception):
    def __init__(self, arg_name):
        super().__init__()
        self.message = f'Missing Config Argument {arg_name}. Make sure you have passed {arg_name} in args parameter of the config object.'

    def __str__(self):
        return self.message


class ConfigReader:
    """Class to read configuration file corresponds to a glue job.
    config = ConfigReader(path=f"/tmp/{args.get("CONFIGPATH")h}", args=args)
    Parameters
        path: the file path.
        config: configuration in string, instead of file.
        args: The arguments provided from the glue arguments. Typically coming from environment variables.
        variables: The variables to be used for templating.
    """

    def __init__(self, path='config.yaml', config: str = None, args={}, variables={}):
        self.path = path
        self.config = config
        self.args = args

        self.region = os.environ.get('AWS_DEFAULT_REGION')
        self.steps = []
        self.stage = args.get('STAGE', '')
        self.variables = variables
        self.job_dir = None
        self.query_dir = None
        self.steps_definition = self.get_steps_definition()

    def _get_file(self, path):
        """Read file from local"""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
                return '\n'.join(lines)
        except Exception as e:
            raise Exception(f'FileNotFound at path {path} {e}')

    def _get_object(self, path):
        """Read file from S3"""
        s3 = boto3.client('s3', region_name=self.region)
        if not self.args.get('BUCKET_NAME', None):
            raise MissingConfigArgument('BUCKET_NAME')
        response = s3.get_object(Bucket=self.args.get('BUCKET_NAME'), Key=path)
        return response['Body'].read().decode('utf-8')

    def get_query(self, path):
        if self.args.get('ISGLUERUNTIME'):
            logging.info('Reading query file from s3 at ', f'{self.query_dir}/{path}')
            return self._get_object(f'{self.query_dir}/{path}')
        else:
            logging.info(f'{self.query_dir}/{path}')
            return self._get_file(f'{self.query_dir}/{path}')

    def get_steps_definition(self):
        config = {}
        self.steps = []
        stage_ = self.stage

        if self.stage == 'prod':
            stage_ = ''
        else:
            stage_ = self.stage

        if self.config:
            try:
                template = Template(self.config)
                if not self.variables:
                    self._parse_variables(config, stage_)

                rendered = template.render(self.variables)
                config = yaml.safe_load(rendered)

            except Exception as e:
                logging.error('Could not parse config ', e)
                raise Exception('Parse Error')
        else:
            try:
                f = open(self.path, 'r')
                template = Template('\n'.join(f.readlines()))

                # First stage config read: get variables
                rendered = template.render()
                config = yaml.safe_load(rendered)

                q_dir = config.get('sql_queries', 'sql_queries')
                j_dir = config.get('glue_jobs', 'glue_jobs')
                u_dir = config.get('udfs', 'udfs')
                t_dir = config.get('tests', 'tests')
                f_dir = config.get('variables_files', 'variables_files')

                if self.stage:
                    self.query_dir = f'{self.stage}/customcode/glue/{q_dir}'
                    self.job_dir = f'{self.stage}/customcode/glue/{j_dir}'
                    self.udf_dir = f'{self.stage}/customcode/glue/{u_dir}'
                    self.test_dir = f'{self.stage}/{t_dir}'
                    self.files_dir = f'{self.stage}/customcode/glue/{f_dir}'

                else:

                    self.query_dir = f'customcode/glue/{q_dir}'
                    self.job_dir = f'customcode/glue/{j_dir}'
                    self.udf_dir = f'customcode/glue/{u_dir}'
                    self.test_dir = f'customcode/glue/{t_dir}'
                    self.files_dir = f'customcode/glue/{f_dir}'

                if not self.variables:
                    self._parse_variables(config, stage_)

                self.variables['stage'] = self.stage
                self.variables['stage_'] = stage_

                # Second stage config read: render with some variables
                rendered = template.render(self.variables)
                config = yaml.safe_load(rendered)
                config['__source__'] = self.path

            except FileNotFoundError:
                logging.error(f'File {self.path} is not found')
                raise
            except Exception:
                logging.error(
                    f'Can not parse [{self.path}] as configuration file. Check the configuration file format.'
                )
                raise

        for step in config.get('steps', []):
            wrapped = StepInterface.create_step(step_input=step, config=config)
            self.steps.append(wrapped)

        return self.steps

    def _parse_variables(self, config, stage_):
        variable_file = config.get('variables', {}).get('file')

        if variable_file:
            try:
                variable_lines = self._get_object(f'{self.files_dir}/{variable_file}')
                template = Template(variable_lines)

                rendered = template.render(stage=self.stage, stage_=stage_)

                self.variables = yaml.safe_load(rendered)
            except Exception as e:

                logging.error('Could not parse variable files ')
                raise e

    def get_variable(self, name):
        return self.variables.get(name)

    def get_step(self, name):
        candidates = [s for s in self.steps if s.name == name]
        if len(candidates):
            return candidates[0]
        return None
