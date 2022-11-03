from aws_ddk_core.config.config import Config
from typing import Dict


class MultiaccountConfig(Config):
    def __int__(self, *args, **kwargs) -> None:
        super.__init__(*args, **kwargs)

    def get_stage_env_id(
            self,
            stage_id: str,
    ) -> str:
        """
        Get environment id representing AWS account and region with specified stage_id.
        Parameters
        ----------
        stage_id : str
            Identifier of the stage
        Returns
        -------
        environment_id : str
        """
        environments = self._config_strategy.get_config(key="environments")

        for env_id, env in environments.items():
            if env.get('stage', {}) == stage_id:
                environment_id = env_id
                break
        else:
            raise ValueError(f'Environment id with stage_id {stage_id} was not found!')

        return environment_id

    def get_env_var_config(
        self,
        environment_id: str,
    ) -> dict:
        """
        Get environment specific variable from config for given environment id.
        Parameters
        ----------
        environment_id : str
            Identifier of the environment
        Returns
        -------
        config : Dict[str, Any]
            Dictionary that contains environmental variables for the given environment
        """
        env_config = self.get_env_config(environment_id)
        return env_config