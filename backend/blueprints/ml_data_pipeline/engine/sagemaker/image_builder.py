import os
import subprocess
from utils.task_group_reader import TaskGroupReader


class SageMakerImageBuilder:
    def __int__(self):
        pass

    @staticmethod
    def build_training_jobs_images(image_uri, region):

        image_uris = []

        main_modules = SageMakerImageBuilder.get_training_jobs_modules()

        try:
            if main_modules:

                token = SageMakerImageBuilder.connect_to_ecr(region)

                for main_module in main_modules:

                    tag_name = SageMakerImageBuilder.build_training_job_image(
                        main_module, image_uri, token
                    )

                    image_uris.append(f'{image_uri}:{tag_name}')

            return image_uris

        except Exception as e:
            print(f'Could not Push image {image_uri} to ECR', e)
            raise e

    @staticmethod
    def build_training_job_image(main_module, image_uri, token=None):
        try:
            tag_name = SageMakerImageBuilder.get_image_tag(main_module)

            SageMakerImageBuilder.build_image_tag(image_uri, main_module, tag_name)

            if token:
                SageMakerImageBuilder.push_image_to_ecr(image_uri, tag_name, token)

            return tag_name

        except Exception as e:
            print(f'Could not build image {image_uri}', e)
            raise e

    @staticmethod
    def build_processing_job_image(image_uri, token=None):
        try:
            SageMakerImageBuilder.build_image_tag(image_uri, '', 'latest')

            if token:
                SageMakerImageBuilder.push_image_to_ecr(image_uri, 'latest', token)

            return 'latest'

        except Exception as e:
            print(f'Could not build image {image_uri}', e)
            raise e

    @staticmethod
    def connect_to_ecr(region):
        print('Connecting to ECR in  region: ', region)
        token = subprocess.getoutput(f'aws ecr get-login-password --region {region}')
        return token

    @staticmethod
    def push_image_to_ecr(image_uri, tag_name, token):
        subprocess.run(
            [f'docker', 'login', '-u AWS', f'-p {token} {image_uri}'],
            stdout=subprocess.PIPE,
        )
        subprocess.run(
            [f'docker', 'push', f'{image_uri}:{tag_name}'], stdout=subprocess.PIPE
        )

    @staticmethod
    def build_image_tag(image_uri, module_path, tag_name):
        print(f'Building tag: {tag_name}')
        dockerfile_path = os.path.realpath(
            os.path.abspath(
                os.path.join(__file__, '..', '..', '..', 'smjobs', 'Dockerfile')
            )
        )
        subprocess.run(
            [
                f'docker',
                'build',
                '--build-arg',
                f'SCRIPT_PATH={module_path}',
                f'-t',
                f'{image_uri}:{tag_name}',
                f'-f {dockerfile_path}',
                '.',
            ],
            stdout=subprocess.PIPE,
        )

    @staticmethod
    def get_image_tag(module_path):
        filename = module_path.split(os.sep)
        if len(filename) == 2:
            filename = (filename[-1]).rsplit('.', 1)[0]
        else:
            filename = (filename[-2] + '_' + filename[-1]).rsplit('.', 1)[0]
        print(filename)
        tag_name = filename.rsplit('.', 1)[0]
        tag_name = tag_name[:128] if len(tag_name) > 128 else tag_name
        return tag_name

    @staticmethod
    def get_training_jobs_modules():
        main_modules = []
        groups = SageMakerImageBuilder.get_groups()
        for group in groups.definition.get('groups', []):
            for j in group.get('jobs', []):
                if j.get('type') == 'sagemaker_training' and j.get('main'):
                    main_modules.append(j.get('main'))
        return main_modules

    @staticmethod
    def get_groups():
        configfile_path = os.path.realpath(
            os.path.abspath(os.path.join(__file__, '..', '..', '..', 'config.yaml'))
        )
        groups = TaskGroupReader(path=configfile_path)
        return groups


if __name__ == '__main__':
    SageMakerImageBuilder.build_training_jobs_images(
        os.getenv('ECR_REPOSITORY_URI'), os.getenv('AWSREGION')
    )
