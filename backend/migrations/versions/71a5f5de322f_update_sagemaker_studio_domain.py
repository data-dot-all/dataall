"""env_mlstudio_domain_table

Revision ID: 71a5f5de322f
Revises: 8c79fb896983
Create Date: 2023-11-29 09:44:04.160286

"""
import os
from sqlalchemy import orm, Column, String, Boolean, ForeignKey, DateTime, and_, inspect
from sqlalchemy.orm import query_expression
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
                new_column_name='sagemakerStudioDomainID',
                nullable=True,
                existing_type=sa.String()
            )
            op.alter_column(
                'sagemaker_studio_domain',
                'SagemakerStudioStatus',
                new_column_name='SagemakerStudioStatus',
                nullable=True,
                existing_type=sa.String()
            )

            op.add_column("sagemaker_studio_domain", Column("sagemakerStudioDomainName", sa.String(), default=True))
            op.add_column("sagemaker_studio_domain", Column("vpcType", sa.String(), default=True))
            op.add_column("sagemaker_studio_domain", Column("vpcId", sa.String(), default=True))
            op.add_column("sagemaker_studio_domain", Column("subnetIds", postgresql.ARRAY(sa.String()), default=True))

            op.create_foreign_key(
                f"fk_sagemaker_studio_domain_env_uri",
                "sagemaker_studio_domain", "environment",
                ["environmentUri"], ["environmentUri"],
            )

            session.commit()
            print("Update of sagemaker_studio_domain table is done")

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
            print("Updating of sagemaker_studio_domain table...")
            op.alter_column(
                'sagemaker_studio_domain',
                'sagemakerStudioDomainID',
                new_column_name='sagemakerStudioDomainID',
                nullable=False,
                existing_type=sa.String()
            )
            op.alter_column(
                'sagemaker_studio_domain',
                'SagemakerStudioStatus',
                new_column_name='SagemakerStudioStatus',
                nullable=False,
                existing_type=sa.String()
            )

            op.drop_column("sagemaker_studio_domain", "sagemakerStudioDomainName")
            op.drop_column("sagemaker_studio_domain", "vpcType")
            op.drop_column("sagemaker_studio_domain", "vpcId")
            op.drop_column("sagemaker_studio_domain", "subnetIds")

            op.drop_constraint("fk_sagemaker_studio_domain_env_uri", "sagemaker_studio_domain")
            
            session.commit()
            print("Update of sagemaker_studio_domain table is done")

    except Exception as exception:
        print('Failed to downgrade due to:', exception)
        raise exception

