This builds an image with [YugabyteDB](https://www.yugabyte.com/yugabytedb/) (re-architected PostgreSQL to be cloud native with horizonztal scalability) configured to be a drop-in replacement of the [PostgreSQL docker image](https://hub.docker.com/_/postgres/) (same behavior, same environment variables)

To run with it, replace `compose/postgres` by `compose/yugabytedb`. 
You can add the port 15433 to access the YugabyteDB console.

You can add more nodes with a service that joins the others with the `--join` option like this:
```
 db-dist:
    build:
      context: compose/yugabytedb
    command: --join=aws-dataall-db-1.aws-dataall_default
    deploy:
      replicas: 2
    depends_on:
     db:
      condition: service_healthy
```
This will replicate data. To connect to all nodes, the PyGreSQL should be replaced by the [Smart Driver](https://docs.yugabyte.com/preview/reference/drivers/python/yugabyte-psycopg2-reference/). If YugabyteDB is deployed from the [AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-whuefqd2j5an4?sr=0-1&ref_=beagle&applicationId=AWSMPContessa) it is not needed when connectin though an HA Proxy.
