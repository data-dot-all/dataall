### Feature or Bugfix
<!-- please choose -->
- Feature
- Bugfix
- Refactoring

### Detail
- <feature1 or bug1>
- <feature2 or bug2>

### Relates
- <URL or Ticket>

### Security
Please answer the questions below briefly where applicable, or write `N/A`. Based on
[OWASP 10](https://owasp.org/Top10/en/).

- Does this PR introduce or modify any input fields or queries - this includes
fetching data from storage outside the application (e.g. a database, an S3 bucket)?
  - Is the input sanitized?
  - What precautions are you taking before deserializing the data you consume?
  - Is injection prevented by parametrizing queries?
  - Have you ensured no `eval` or similar functions are used?
- Does this PR introduce any functionality or component that requires authorization?
  - How have you ensured it respects the existing AuthN/AuthZ mechanisms?
  - Are you logging failed auth attempts?
- Are you using or adding any cryptographic features?
  - Do you use a standard proven implementations?
  - Are the used keys controlled by the customer? Where are they stored?
- Are you introducing any new policies/roles/users?
  - Have you used the least-privilege principle? How?


By submitting this pull request, I confirm that my contribution is made under the terms of the Apache 2.0 license.
