# Maintainer Responsibilities

- [Overview](#overview)
- [Current Maintainers](#current-maintainers)
- [Maintainer Responsibilities](#maintainer-responsibilities)
    - [Uphold Code of Conduct](#uphold-code-of-conduct)
    - [Prioritize Security](#prioritize-security)
    - [Review Pull Requests](#review-pull-requests)
    - [Triage Open Issues](#triage-open-issues)
        - [Automatically Label Issues](#automatically-label-issues)
    - [Be Responsive](#be-responsive)
    - [Maintain Overall Health of the Repo](#maintain-overall-health-of-the-repo)
        - [Keep Dependencies up to Date](#keep-dependencies-up-to-date)
    - [Manage Roadmap](#manage-roadmap)
    - [Add Continuous Integration Checks](#add-continuous-integration-checks)
    - [Use Semver](#use-semver)
    - [Release Frequently](#release-frequently)
    - [Promote Other Maintainers](#promote-other-maintainers)
    - [Describe the Repo](#describe-the-repo)
- [Becoming a Maintainer](#becoming-a-maintainer)
    - [Nomination](#nomination)
    - [Interest](#interest)
    - [Addition](#addition)
- [Removing a Maintainer](#removing-a-maintainer)
    - [Moving On](#moving-on)
    - [Inactivity](#inactivity)
    - [Negative Impact on the Project](#negative-impact-on-the-project)

## Overview

This document explains who maintainers are, what they do in the data.all project, and how they should be doing it. 
If you're interested in contributing, see [Becoming a Maintainer](#becoming-a-maintainer).

## Current Maintainers

The current maintainers are listed in [MAINTAINERS.md](MAINTAINERS.md).

## Maintainer Responsibilities

Maintainers are active and visible members of the community, and have [maintain-level permissions on a repository](https://docs.github.com/en/organizations/managing-access-to-your-organizations-repositories/repository-permission-levels-for-an-organization). Use those privileges to serve the community and evolve code as follows.

### Uphold Code of Conduct

Model the behavior set forward by the [Code of Conduct](CODE_OF_CONDUCT.md) and raise any violations to other maintainers.

### Prioritize Security

Security is our number one priority. Maintainer's Github keys must be password protected securely and any reported security vulnerabilities are addressed before features or bugs.

Note that this repository is monitored and supported 24/7 by Amazon Security, see [Reporting a Vulnerability](SECURITY.md) for details.

### Review Pull Requests

Review pull requests regularly, comment, suggest, reject, merge and close. Accept only high quality pull-requests. Provide code reviews and guidance on incoming pull requests. Don't let PRs be stale and do your best to be helpful to contributors.

### Triage Open Issues

Manage labels, review issues regularly, and triage by labelling them.

We use key value labels, use the `priority:`, `type:`, `effort:` and `status:` when triaging issues.

Use the `good first issue` label to let new community members know where to start and `blocker` for issues that scare you or need immediate attention. Request for more information from a submitter if an issue is not clear. Create new labels as needed by the project.

### Be Responsive

Respond to enhancement requests, and forum posts. Allocate time to reviewing and commenting on issues and conversations as they come in.

### Maintain Overall Health of the Repo

Keep the `main` branch at production quality at all times. Backport features as needed. Cut release branches and tags to enable future patches.

#### Keep Dependencies up to Date

Maintaining up-to-date dependencies on third party projects reduces the risk of security vulnerabilities. As 
[recommended](https://github.com/ossf/scorecard/blob/main/docs/checks.md#dependency-update-tool) by 
The Open Source Security Foundation (OpenSSF)  we use Dependabot, which is integrated with GitHub. Dependabot does not 
have any centralized management dashboard, so maintainers may use tags or other PR filters to track pending updates.

### Manage Roadmap

Ensure the repo highlights features that should be elevated to the project roadmap. Be clear about the feature’s status, 
priority, target version, and whether or not it should be elevated to the roadmap. Any feature that you want highlighted 
on the data.all Roadmap should be tagged with "roadmap".

### Add Continuous Integration Checks

Add integration checks that validate pull requests and pushes to ease the burden on Pull Request reviewers.

### Use Semver

Use and enforce [semantic versioning](https://semver.org/) and do not let breaking changes be made outside of major releases.

### Release Frequently

Make frequent project releases to the community.

### Promote Other Maintainers

Assist, add, and remove [MAINTAINERS](MAINTAINERS.md). Exercise good judgement, and propose high quality contributors to become co-maintainers. See [Becoming a Maintainer](#becoming-a-maintainer) for more information.

### Describe the Repo

Make sure the repo has a well-written, accurate, and complete description.
## Becoming a Maintainer

You can become a maintainer by actively [contributing](CONTRIBUTING.md) to the project, and being nominated by an existing maintainer.

### Nomination

Any current maintainer starts a private conversation (e-mail or IM) with all other maintainers to discuss nomination using the template below. 
In order to be approved, at least three positive (+1) maintainer votes are necessary (or all maintainers, if there are fewer than 3), and no vetoes (-1).

The nomination should clearly identify the person with their real name and a link to their GitHub profile, and the 
rationale for the nomination, with concrete example contributions.

### Interest

Upon receiving at least three positive (+1) maintainer votes, and no vetoes (-1), from existing maintainers after a one week period, the nominating maintainer asks the nominee whether they might be interested in becoming a maintainer on the repository via private e-mail message.

> This is great work! Based on your valuable contribution and ongoing engagement with the project, the current maintainers invite you to become a co-maintainer for this project. Please respond and let us know if you accept the invitation to become maintainer.

Individuals accept the nomination by replying, or commenting, for example _"Thank you! I would love to."_

### Addition

Upon receiving three positive (+1) maintainer votes, and no vetoes (-1), from other maintainers, and after having privately confirmed interest with the nominee, the maintainer opens a pull request adding the proposed co-maintainer to MAINTAINERS.md. The pull request is approved and merged.

> _Content from the above nomination._
>
> The maintainers have voted and agreed to this nomination.

Finally, the new maintainer's permissions are adjusted to reflect their new role.

## Removing a Maintainer

Removing a maintainer is a disruptive action that the community of maintainers should not undertake lightly. There are several reasons that a maintainer may be removed from the project including:

- **Moving On.** There are plenty of reasons that might cause someone to want to take a step back or even a hiatus from a project.
- **Inactivity.** Although maintainer status never expires, other maintainers may choose to remove anyone who has been inactive for a prolonged time (over six months).
- **Violating the [code of conduct](./CODE_OF_CONDUCT.md)** or taking other actions that negatively impact the project.

A maintainer can choose to leave the project at any time, with or without reason, by making a pull request to move themselves to the "Emeritus" section of MAINTAINERS.md, and asking an existing maintainer to remove their permissions.

A maintainer can be removed by other maintainers, as set out in [governance](./GOVERNANCE.md).  Once the decision has been made to remove a maintainer, a pull request will be raised to move them to the "Emeritus" section of MAINTAINERS.md, and asking the existing maintainers will remove their permissions.
