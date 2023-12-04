"""env_mlstudio_domain_table

Revision ID: 71a5f5de322f
Revises: 8c79fb896983
Create Date: 2023-11-29 09:44:04.160286

"""
import os
from sqlalchemy import orm, Column, String, Boolean, ForeignKey, and_
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
from alembic import op

from sqlalchemy.dialects import postgresql
from dataall.base.db import get_engine, has_table
from dataall.base.db import utils, Resource

# revision identifiers, used by Alembic.
revision = '71a5f5de322f'
down_revision = '8c79fb896983'
branch_labels = None
depends_on = None

Base = declarative_base()


class Environment(Resource, Base):
    __tablename__ = "environment"
    environmentUri = Column(String, primary_key=True)
    AwsAccountId = Column(Boolean)
    region = Column(Boolean)


class EnvironmentParameter(Base):
    __tablename__ = 'environment_parameters'
    environmentUri = Column(String, primary_key=True)
    key = Column('paramKey', String, primary_key=True)
    value = Column('paramValue', String, nullable=True)


class SagemakerStudioDomain(Resource, Base):
    __tablename__ = 'sagemaker_studio_domain'
    environmentUri = Column(String, ForeignKey("environment.environmentUri"))
    sagemakerStudioUri = Column(
        String, primary_key=True, default=utils.uuid('sagemakerstudio')
    )
    sagemakerStudioDomainID = Column(String, nullable=True)
    SagemakerStudioStatus = Column(String, nullable=True)
    sagemakerStudioDomainName = Column(String, nullable=False)
    AWSAccountId = Column(String, nullable=False)
    DefaultDomainRoleName = Column(String, nullable=False)
    region = Column(String, default='eu-west-1')
    vpcType = Column(String, nullable=True)


def upgrade():
    """
    The script does the following migration:
        1) update of the sagemaker_studio_domain table to include SageMaker Studio Domain VPC Information
    """
    try:
        envname = os.getenv('envname', 'local')
        engine = get_engine(envname=envname).engine

        bind = op.get_bind()
        session = orm.Session(bind=bind)

        if has_table('sagemaker_studio_domain', engine):
            print("Updating sagemaker_studio_domain table...")
            op.alter_column(
                'sagemaker_studio_domain',
                'sagemakerStudioDomainID',
                nullable=True,
                existing_type=sa.String()
            )
            op.alter_column(
                'sagemaker_studio_domain',
                'SagemakerStudioStatus',
                nullable=True,
                existing_type=sa.String()
            )
            op.alter_column(
                'sagemaker_studio_domain',
                'RoleArn',
                new_column_name='DefaultDomainRoleName',
                nullable=False,
                existing_type=sa.String()
            )

            op.add_column("sagemaker_studio_domain", Column("sagemakerStudioDomainName", sa.String(), nullable=False))
            op.add_column("sagemaker_studio_domain", Column("vpcType", sa.String(), nullable=True))
            op.add_column("sagemaker_studio_domain", Column("vpcId", sa.String(), nullable=True))
            op.add_column("sagemaker_studio_domain", Column("subnetIds", postgresql.ARRAY(sa.String()), nullable=True))

            op.create_foreign_key(
                "fk_sagemaker_studio_domain_env_uri",
                "sagemaker_studio_domain", "environment",
                ["environmentUri"], ["environmentUri"],
            )
        else:
            print("No sagemaker_studio_domain table found, creating...")
            op.create_table(
                'sagemaker_studio_domain',
                sa.Column('label', sa.String(), nullable=False),
                sa.Column('name', sa.String(), nullable=False),
                sa.Column('owner', sa.String(), nullable=False),
                sa.Column('created', sa.DateTime(), nullable=True),
                sa.Column('updated', sa.DateTime(), nullable=True),
                sa.Column('deleted', sa.DateTime(), nullable=True),
                sa.Column('description', sa.String(), nullable=True),
                sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
                sa.Column('environmentUri', sa.String(), nullable=False),
                sa.Column('sagemakerStudioUri', sa.String(), nullable=False),
                sa.Column('sagemakerStudioDomainID', sa.String(), nullable=True),
                sa.Column('SagemakerStudioStatus', sa.String(), nullable=True),
                sa.Column('AWSAccountId', sa.String(), nullable=False),
                sa.Column('DefaultDomainRoleName', sa.String(), nullable=False),
                sa.Column('sagemakerStudioDomainName', sa.String(), nullable=False),
                sa.Column('vpcType', sa.String(), nullable=True),
                sa.Column('vpcId', sa.String(), nullable=True),
                sa.Column('subnetIds', postgresql.ARRAY(sa.String()), nullable=True),
                sa.Column('region', sa.String(), nullable=True),
                sa.PrimaryKeyConstraint('sagemakerStudioUri'),
                sa.ForeignKeyConstraint(columns=['environmentUri'], refcolumns=['environment.environmentUri']),
            )

        print("Update sagemaker_studio_domain table done.")
        print("Filling sagemaker_studio_domain table with environments with mlstudio enabled...")

        env_mlstudio_parameters: [EnvironmentParameter] = session.query(EnvironmentParameter).filter(
            and_(
                EnvironmentParameter.key == "mlStudiosEnabled",
                EnvironmentParameter.value == "true"
            )
        ).all()
        for param in env_mlstudio_parameters:
            env: Environment = session.query(Environment).filter(
                Environment.environmentUri == param.environmentUri
            ).first()

            domain = SagemakerStudioDomain(
                label=f"SagemakerStudioDomain-{env.region}-{env.AwsAccountId}",
                owner=env.owner,
                description='No description provided',
                environmentUri=env.environmentUri,
                AWSAccountId=env.AwsAccountId,
                region=env.region,
                DefaultDomainRoleName="RoleSagemakerStudioUsers",
                sagemakerStudioDomainName=f"SagemakerStudioDomain-{env.region}-{env.AwsAccountId}",
                vpcType="unknown"
            )
            session.add(domain)
        session.flush()

        session.commit()
        print("Fill of sagemaker_studio_domain table is done")

    except Exception as exception:
        print('Failed to upgrade due to:', exception)
        raise exception


def downgrade():
    try:
        envname = os.getenv('envname', 'local')
        engine = get_engine(envname=envname).engine

        bind = op.get_bind()
        session = orm.Session(bind=bind)

        if has_table('sagemaker_studio_domain', engine):
            print("Dropping sagemaker_studio_domain table...")
            op.drop_table("sagemaker_studio_domain")
            session.commit()
            print("Dropped of sagemaker_studio_domain table")

    except Exception as exception:
        print('Failed to downgrade due to:', exception)
        raise exception
