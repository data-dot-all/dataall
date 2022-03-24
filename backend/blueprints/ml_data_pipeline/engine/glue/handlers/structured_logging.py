from datetime import date, datetime
import json
import logging
import time
import traceback

import boto3


class StructuredLogger:
    def __init__(self, step=1):
        logging.basicConfig(
            level=logging.INFO, format="%(levelname)s: %(asctime)s: %(message)s"
        )
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.step = step
        self.version = 2

    def next_step(self):
        self.step += 1

    def skip(self, reason, message={}, eventMessage={}):
        self.logger.error(
            "Skipping. %s",
            json.dumps(
                {
                    "logVersion": self.version,
                    "step": self.step,
                    "status": "skipEvent",
                    "reason": reason,
                    "message": message,
                    "eventMessage": eventMessage,
                },
                indent=2,
                default=str,
            ),
        )

    def s3_skip_wrong_bucket(self, actualBucket, desiredBucket, eventMessage={}):
        self.skip(
            "Wrong S3 bucket",
            {
                "messageType": "S3Bucket",
                "messageVersion": 1,
                "actualBucket": actualBucket,
                "desiredBucket": desiredBucket,
            },
            eventMessage,
        )

    def s3_skip_wrong_key(self, actualKey, desiredKey, eventMessage={}):
        self.skip(
            "Wrong S3 key",
            {
                "messageType": "S3Key",
                "messageVersion": 1,
                "actualKey": actualKey,
                "desiredKey": desiredKey,
            },
            eventMessage,
        )

    def sqs_skip_no_message(self, queueUrl, eventMessage={}):
        self.skip(
            "No SQS message",
            {"messageType": "SQSNoMessage", "messageVersion": 2, "queueUrl": queueUrl},
            eventMessage,
        )

    def glue_skip_no_free_resources(self, jobName, eventMessage={}):
        self.skip(
            "No free Glue resources",
            {
                "messageType": "GlueNoFreeResources",
                "messageVersion": 1,
                "jobName": jobName,
            },
            eventMessage,
        )

    def function_start(
        self, reason, completeStatus, function, *args, eventMessage={}, **kwargs
    ):
        callerIdentity = boto3.client("sts").get_caller_identity()
        startTime = time.time()

        self.logger.info(
            "Starting function. %s",
            json.dumps(
                {
                    "logVersion": self.version,
                    "step": self.step,
                    "status": "functionStart",
                    "reason": reason,
                    "message": {
                        "messageType": "functionStart",
                        "messageVersion": 3,
                        "function": function.__name__,
                        "callerIdentity": callerIdentity,
                        "startTime": startTime,
                        "args": args,
                        "kwargs": kwargs,
                    },
                    "eventMessage": eventMessage,
                },
                indent=2,
                default=str,
            ),
        )

        try:
            retval = function(*args, **kwargs)
            elapsedTime = time.time() - startTime
            self.function_complete(
                completeStatus,
                function.__name__,
                retval,
                startTime,
                elapsedTime,
                callerIdentity,
                *args,
                **kwargs,
                eventMessage=eventMessage
            )
            return retval
        except Exception as error:
            self.function_fail(
                function.__name__,
                str(error),
                traceback.format_exc(),
                startTime,
                callerIdentity,
                *args,
                eventMessage=eventMessage,
                **kwargs
            )
            raise error
        return retval

    def function_complete(
        self,
        reason,
        functionName,
        returnValue,
        startTime,
        elapsedTime,
        callerIdentity,
        *args,
        eventMessage={},
        **kwargs
    ):
        self.logger.info(
            "Completing function. %s",
            json.dumps(
                {
                    "logVersion": self.version,
                    "step": self.step,
                    "status": "functionComplete",
                    "reason": reason,
                    "message": {
                        "messageType": "functionComplete",
                        "messageVersion": 3,
                        "function": functionName,
                        "callerIdentity": callerIdentity,
                        "startTime": startTime,
                        "elapsedTime": elapsedTime,
                        "returnValue": returnValue,
                        "args": args,
                        "kwargs": kwargs,
                    },
                    "eventMessage": eventMessage,
                },
                indent=2,
                default=str,
            ),
        )

    def function_fail(
        self,
        functionName,
        errorMessage,
        traceback,
        startTime,
        callerIdentity,
        *args,
        eventMessage={},
        **kwargs
    ):
        self.logger.error(
            "Failing function. %s",
            json.dumps(
                {
                    "logVersion": self.version,
                    "step": self.step,
                    "status": "functionFail",
                    "reason": "unrecoverable error encountered",
                    "message": {
                        "messageType": "functionFail",
                        "messageVersion": 3,
                        "function": functionName,
                        "callerIdentity": callerIdentity,
                        "startTime": startTime,
                        "elapsedTime": time.time() - startTime,
                        "errorMessage": errorMessage,
                        "traceback": traceback,
                        "args": args,
                        "kwargs": kwargs,
                    },
                    "eventMessage": eventMessage,
                },
                indent=2,
                default=str,
            ),
        )

    def info(self, *args, **kwargs):
        self.logger.info(*args, **kwargs)

    def error(self, *args, **kwargs):
        self.logger.error(*args, **kwargs)
