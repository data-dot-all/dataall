from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_sns, aws_sns_subscriptions


def make_publish_to_sns_task(stack, job):
    """Makes SNS publish task.
    It reads the message configured and publishes it in an SNS topic
    :param stack the enclosing step function stack
    :job the job configuration
    """
    topic_arn = f"arn:aws:sns:{stack.pipeline_region}:{stack.accountid}:{job.get('config').get('topic_name')}"
    topic = aws_sns.Topic.from_topic_arn(
        stack,
        id=f"{stack.pipeline_name}-{job.get('config').get('topic_name')}-{job.get('name')}",
        topic_arn=topic_arn,
    )
    task = tasks.SnsPublish(
        stack,
        "SNS: " + job["name"],
        message=stepfunctions.TaskInput.from_text(job.get("config").get("message")),
        topic=topic,
    )

    return task
