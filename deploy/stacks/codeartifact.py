from aws_cdk import aws_codeartifact as codeartifact, aws_iam as iam, NestedStack


class CodeArtifactStack(NestedStack):
    def __init__(
        self,
        scope,
        id,
        target_envs: [] = None,
        resource_prefix: str = 'dataall',
        git_branch: str = None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        domain_dict = dict(domain_name=f'{resource_prefix}-domain-{git_branch}')
        if target_envs:
            principals: [iam.AccountPrincipal] = [iam.AccountPrincipal(account['account']) for account in target_envs]
            principals.append(iam.AccountPrincipal(self.account))
            domain_policy = iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            'codeartifact:GetDomainPermissionsPolicy',
                            'codeartifact:ListRepositoriesInDomain',
                            'codeartifact:GetAuthorizationToken',
                            'codeartifact:DescribeDomain',
                            'codeartifact:CreateRepository',
                        ],
                        principals=principals,
                        resources=['*'],
                    )
                ]
            )
            domain_dict['permissions_policy_document'] = domain_policy

            pip_repo_policy = iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            'codeartifact:DescribePackageVersion',
                            'codeartifact:DescribeRepository',
                            'codeartifact:GetPackageVersionReadme',
                            'codeartifact:GetRepositoryEndpoint',
                            'codeartifact:ListPackageVersionAssets',
                            'codeartifact:ListPackageVersionDependencies',
                            'codeartifact:ListPackageVersions',
                            'codeartifact:ListPackages',
                            'codeartifact:ReadFromRepository',
                        ],
                        principals=principals,
                        resources=['*'],
                    )
                ]
            )

        domain = codeartifact.CfnDomain(self, 'CodeArtifactDomain', **domain_dict)
        npm_repo = codeartifact.CfnRepository(
            self,
            'CodeArtifactNpmRepo',
            domain_name=domain.domain_name,
            repository_name=f'{resource_prefix}-npm-store',
            external_connections=[
                'public:npmjs',
            ],
        )
        npm_repo.add_override('Properties.DomainName', domain.domain_name)
        npm_repo.add_depends_on(domain)

        pip_repo = codeartifact.CfnRepository(
            self,
            'CodeArtifactPipRepo',
            domain_name=domain.domain_name,
            repository_name=f'{resource_prefix}-pypi-store',
            external_connections=[
                'public:pypi',
            ],
            permissions_policy_document=pip_repo_policy,
        )
        pip_repo.add_override('Properties.DomainName', domain.domain_name)
        pip_repo.add_depends_on(domain)

        self.domain = domain
        self.npm_repo = npm_repo
        self.pip_repo = pip_repo

    @property
    def codeartifact_domain_name(self) -> str:
        return self.domain.domain_name

    @property
    def codeartifact_pip_repo_name(self) -> str:
        return self.pip_repo.repository_name

    @property
    def codeartifact_npm_repo_name(self) -> str:
        return self.npm_repo.repository_name
