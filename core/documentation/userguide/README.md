# User guide for data.all

This folder contains information for developers to add content to the user guide documentation accessible from the UI.

![documentation](documentation.png)
## Developing documentation locally
if you already have a virtualenv for the data.all project and
you have activate the virtualenv shell, simply cd into the documentation/userguide folder and run:

```bash
> cd documentation/userguide
> pip install -r requirements.txt
> mkdocs serve

```

The last command will run a local mkdocs server running on port 8000.

### Graphql:

the graphql md has been generated using the npm package: graphql-markdown

```bash
npm install graphql-markdown -g
graphql-markdown https://localhost:3000/graphql > graphql.md
```
