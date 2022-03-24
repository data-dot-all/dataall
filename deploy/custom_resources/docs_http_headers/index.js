'use strict';
exports.handler = (event, context, callback) => {
//Get contents of response
    const response = event.Records[0].cf.response;
    console.info("EVENT\n" + JSON.stringify(event, null, 2))
    console.info("RECORDS\n" + JSON.stringify(event.Records[0], null, 2))
    console.info("cf\n" + JSON.stringify(event.Records[0].cf, null, 2))
    console.info("cfresponse\n" + JSON.stringify(event.Records[0].cf.response, null, 2))
    const headers = response.headers;
    console.info("headers\n" + JSON.stringify(response.headers, null, 2))
//Set new headers
    headers['content-security-policy'] = [{key: 'Content-Security-Policy', value: "script-src  https://code.jquery.com https://stackpath.bootstrapcdn.com 'self' 'unsafe-inline' ;style-src https://fonts.googleapis.com 'self' 'unsafe-inline';font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com data: 'unsafe-inline';img-src 'self' data: 'unsafe-inline';"}];
//Return modified response
    callback(null, response);
};