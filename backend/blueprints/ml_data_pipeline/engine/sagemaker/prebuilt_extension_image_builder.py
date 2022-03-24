import os
import subprocess

from utils.task_group_reader import TaskGroupReader


class PrebuiltExtensionImageBuilder:
    def __int__(self):
        pass

    @staticmethod
    def build_training_jobs_images(image_uri, region):
        print('Build training glue_jobs images')

        image_uris = []

        docker_infos = PrebuiltExtensionImageBuilder.get_prebuilt_docker_infos()

        print('Detecting docker_infos ', docker_infos)

        try:
            if docker_infos:

                token = PrebuiltExtensionImageBuilder.connect_to_ecr(region)

                for docker_info in docker_infos:

                    base_container_server = docker_info['base_server']
                    base_image = docker_info['base_repository']
                    base_container_tag = docker_info['base_tag']

                    base_image_uri = '{}/{}:{}'.format(
                        base_container_server, base_image, base_container_tag
                    )

                    main_module = docker_info['module']
                    entry_point = docker_info['entry_point']
                    dockerfile = docker_info.get('dockerfile')

                    print(
                        'To login to {} to obtain the base container'.format(
                            base_container_server
                        )
                    )
                    subprocess.getoutput(
                        f'aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {base_container_server}'
                    )

                    print('Logged in to {}'.format(base_container_server))

                    print(
                        f'To build training job: URI: {image_uri}, Base_image: {base_image} , main_module: {main_module}, entry_point: {entry_point}'
                    )

                    tag_name = PrebuiltExtensionImageBuilder.build_training_job_image(
                        main_module,
                        base_image_uri,
                        image_uri,
                        entry_point,
                        dockerfile,
                        token,
                    )

                    image_uris.append(f'{image_uri}:{tag_name}')

            for uri in image_uris:
                print(f'Image URI {uri} is pushed')
            return image_uris

        except Exception as e:
            print(f'Could not Push image {image_uri} to ECR', e)
            raise e

    @staticmethod
    def image_uri_from_main_module(main_module):
        return (
            os.getenv('ECR_REPOSITORY')
            + ':'
            + PrebuiltExtensionImageBuilder.get_image_tag(main_module)
        )

    @staticmethod
    def build_training_job_image(
        main_module, base_image, image_uri, entry_point, dockerfile, token=None
    ):
        try:
            tag_name = PrebuiltExtensionImageBuilder.get_image_tag(main_module)
            print('Obtain tag {} from {}'.format(tag_name, main_module))
            PrebuiltExtensionImageBuilder.build_image_tag(
                image_uri, base_image, main_module, entry_point, tag_name, dockerfile
            )

            if token:
                print(
                    'To push image  {} to ECR with tag {} '.format(image_uri, tag_name)
                )
                PrebuiltExtensionImageBuilder.push_image_to_ecr(
                    image_uri, tag_name, token
                )

            return tag_name

        except Exception as e:
            print(f'Could not build image {image_uri}', e)
            raise e

    @staticmethod
    def connect_to_ecr(region):
        print('Connecting to ECR in  region: ', region)
        import subprocess

        return subprocess.getoutput(f'aws ecr get-login-password --region {region}')

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
    def build_image_tag(
        image_uri,
        base_image,
        module_path,
        entry_point,
        tag_name,
        dockerfile='Prebuilt_Dockerfile',
    ):

        dfile = dockerfile if dockerfile else 'Prebuilt_Dockerfile'
        print(
            f'Building module: {module_path} - {entry_point} - {tag_name}, for base image {base_image}, and dockerfile {dockerfile}'
        )

        dockerfile_path = os.path.realpath(
            os.path.abspath(
                os.path.join(
                    __file__, '..', '..', '..', 'sagemaker_jobs', 'dockerfiles', dfile
                )
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
                f'--build-arg BASE_CONTAINER={base_image}',
                f'--build-arg ENTRY_POINT={entry_point}',
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
        tag_name = filename.rsplit('.', 1)[0]
        tag_name = tag_name[:128] if len(tag_name) > 128 else tag_name
        return tag_name

    @staticmethod
    def get_prebuilt_docker_infos_of_group(group, docker_infos):
        for j in group.get('jobs', []):
            if j.get('type') == 'sagemaker_training' and j['config'].get(
                'algorithm', {}
            ).get('pre_built'):
                algorithm = j['config']['algorithm']['pre_built']
                docker_infos.append(algorithm)
            elif j.get('type') == 'choice':
                for choice in j.get('choices', []):
                    for sub_group in choice.get('groups', []):
                        PrebuiltExtensionImageBuilder.get_prebuilt_docker_infos_of_group(
                            sub_group, docker_infos
                        )

    @staticmethod
    def get_prebuilt_docker_infos():
        docker_infos = []
        groups = PrebuiltExtensionImageBuilder.get_groups()
        for group in groups.definition.get('groups', []):
            PrebuiltExtensionImageBuilder.get_prebuilt_docker_infos_of_group(
                group, docker_infos
            )
        return docker_infos

    @staticmethod
    def get_groups():
        configfile_path = os.path.realpath(
            os.path.abspath(os.path.join(__file__, '..', '..', '..', 'config.yaml'))
        )
        groups = TaskGroupReader(path=configfile_path)
        return groups


if __name__ == '__main__':
    PrebuiltExtensionImageBuilder.build_training_jobs_images(
        os.getenv('ECR_REPOSITORY'), os.getenv('AWSREGION')
    )
