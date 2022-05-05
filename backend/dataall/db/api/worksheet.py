import logging

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from .. import exceptions, models, paginate, permissions
from . import ResourcePolicy, has_resource_perm, has_tenant_perm

logger = logging.getLogger(__name__)


class Worksheet:
    @staticmethod
    def get_worksheet_by_uri(session, uri: str) -> models.Worksheet:
        if not uri:
            raise exceptions.RequiredParameter(param_name="worksheetUri")
        worksheet = Worksheet.find_worksheet_by_uri(session, uri)
        if not worksheet:
            raise exceptions.ObjectNotFound("Worksheet", uri)
        return worksheet

    @staticmethod
    def find_worksheet_by_uri(session, uri) -> models.Worksheet:
        return session.query(models.Worksheet).get(uri)

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_WORKSHEETS)
    def create_worksheet(session, username, groups, uri, data=None, check_perm=None) -> models.Worksheet:
        if not data:
            raise exceptions.RequiredParameter(data)
        if not data.get("SamlAdminGroupName"):
            raise exceptions.RequiredParameter("groupUri")
        if not data.get("label"):
            raise exceptions.RequiredParameter("label")

        worksheet = models.Worksheet(
            owner=username,
            label=data.get("label"),
            description=data.get("description", "No description provided"),
            tags=data.get("tags"),
            chartConfig={"dimensions": [], "measures": [], "chartType": "bar"},
            SamlAdminGroupName=data["SamlAdminGroupName"],
        )
        session.add(worksheet)
        session.commit()

        activity = models.Activity(
            action="WORKSHEET:CREATE",
            label="WORKSHEET:CREATE",
            owner=username,
            summary=f"{username} created worksheet {worksheet.name} ",
            targetUri=worksheet.worksheetUri,
            targetType="worksheet",
        )
        session.add(activity)

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data["SamlAdminGroupName"],
            permissions=permissions.WORKSHEET_ALL,
            resource_uri=worksheet.worksheetUri,
            resource_type=models.Worksheet.__name__,
        )
        return worksheet

    @staticmethod
    @has_resource_perm(permissions.UPDATE_WORKSHEET)
    def update_worksheet(session, username, groups, uri, data=None, check_perm=None):
        worksheet = Worksheet.get_worksheet_by_uri(session, uri)
        for field in data.keys():
            setattr(worksheet, field, data.get(field))
        session.commit()

        activity = models.Activity(
            action="WORKSHEET:UPDATE",
            label="WORKSHEET:UPDATE",
            owner=username,
            summary=f"{username} updated worksheet {worksheet.name} ",
            targetUri=worksheet.worksheetUri,
            targetType="worksheet",
        )
        session.add(activity)
        return worksheet

    @staticmethod
    @has_resource_perm(permissions.GET_WORKSHEET)
    def get_worksheet(session, username, groups, uri, data=None, check_perm=None):
        worksheet = Worksheet.get_worksheet_by_uri(session, uri)
        return worksheet

    @staticmethod
    def query_user_worksheets(session, username, groups, filter) -> Query:
        query = session.query(models.Worksheet).filter(
            or_(
                models.Worksheet.owner == username,
                models.Worksheet.SamlAdminGroupName.in_(groups),
            )
        )
        if filter and filter.get("term"):
            query = query.filter(
                or_(
                    models.Worksheet.label.ilike("%" + filter.get("term") + "%"),
                    models.Worksheet.description.ilike("%" + filter.get("term") + "%"),
                    models.Worksheet.tags.contains(f"{{{filter.get('term')}}}"),
                )
            )
        return query

    @staticmethod
    def paginated_user_worksheets(session, username, groups, uri, data=None, check_perm=None) -> dict:
        return paginate(
            query=Worksheet.query_user_worksheets(session, username, groups, data),
            page=data.get("page", 1),
            page_size=data.get("pageSize", 10),
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.SHARE_WORKSHEET)
    def share_worksheet(session, username, groups, uri, data=None, check_perm=None) -> models.WorksheetShare:
        share = (
            session.query(models.WorksheetShare)
            .filter(
                and_(
                    models.WorksheetShare.worksheetUri == uri,
                    models.WorksheetShare.principalId == data.get("principalId"),
                    models.WorksheetShare.principalType == data.get("principalType"),
                )
            )
            .first()
        )

        if not share:
            share = models.WorksheetShare(
                worksheetUri=uri,
                principalType=data["principalType"],
                principalId=data["principalId"],
                canEdit=data.get("canEdit", True),
                owner=username,
            )
            session.add(share)

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=data["principalId"],
                permissions=permissions.WORKSHEET_SHARED,
                resource_uri=uri,
                resource_type=models.Worksheet.__name__,
            )
        return share

    @staticmethod
    @has_resource_perm(permissions.SHARE_WORKSHEET)
    def update_share_worksheet(session, username, groups, uri, data=None, check_perm=None) -> models.WorksheetShare:
        share: models.WorksheetShare = data["share"]
        share.canEdit = data["canEdit"]
        worksheet = Worksheet.get_worksheet_by_uri(session, uri)
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=share.principalId,
            permissions=permissions.WORKSHEET_SHARED,
            resource_uri=uri,
            resource_type=models.Worksheet.__name__,
        )
        return share

    @staticmethod
    @has_resource_perm(permissions.SHARE_WORKSHEET)
    def delete_share_worksheet(session, username, groups, uri, data=None, check_perm=None) -> bool:
        share: models.WorksheetShare = data["share"]
        ResourcePolicy.delete_resource_policy(
            session=session,
            group=share.principalId,
            resource_uri=uri,
            resource_type=models.Worksheet.__name__,
        )
        session.delete(share)
        session.commit()
        return True

    @staticmethod
    @has_resource_perm(permissions.DELETE_WORKSHEET)
    def delete_worksheet(session, username, groups, uri, data=None, check_perm=None) -> bool:
        worksheet = Worksheet.get_worksheet_by_uri(session, uri)
        session.delete(worksheet)
        ResourcePolicy.delete_resource_policy(
            session=session,
            group=worksheet.SamlAdminGroupName,
            resource_uri=uri,
            resource_type=models.Worksheet.__name__,
        )
        return True
