import {util} from '@aws-appsync/utils';

/**
 * Sends a request to a Lambda function. Passes all information about the request from the `info` object.
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {import('@aws-appsync/utils').LambdaRequest} the request
 */
export function request(ctx) {
    return {
        operation: 'Invoke',
        payload: ctx,
    };
}

/**
 * Process a Lambda function response
 * @param {import('@aws-appsync/utils').Context} ctx the context
 * @returns {*} the Lambda function response
 */
export function response(ctx) {
    const {result, error} = ctx;
    if (error) {
        util.error(error.message, error.type, result);
    }
    return result;
}
