# Glue job config.yaml

```yaml
# An example YAML file with all types of glue job handlers
steps:
  - name: examplestep
    type: obfuscate
    config:
      obfuscate_cols: "emailaddress,name"
      target: rawdatainput

```

# Custom Handlers -  create new handlers
 Steps:
1. Under engine/glue/handlers create (or copy/paste) a python script for your handler
2. Define the glue step input. the type corresponds to the type that will be used to call this glue handler and the properties are the variables under config in the glue yaml file. Notice that it is possible to specify required inputs.
```
@Step(
    type="obfuscate",
    props_schema={
        "type":  "object",
        "properties":{
            "obfuscate_cols" : {"type": "string"},
            "target": {"type": "string"}
        }
    }
)
```
3. Define

4. Add the handler class to the _init_.py file of the handlers
