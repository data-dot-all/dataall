> `gql ` is a tiny package for code-first development of GraphQL APIs.
It allows developers to define their schema using a pythonic interface, and
brings a simple visitor mechanism for schema extension.

# Simple example

`gql` maps GraphQL constructs to Python classes, that can be defined, manipulated and extended.

```python
import dataall.base.api.gql as gql

Post = gql.ObjectType(
    name="Post",
    fields=[
        gql.Field(name="id", type=gql.String),
        gql.Field(name="name", type=gql.NonNullableType(gql.String)),
        gql.Field(name="comments", type=gql.ArrayType(gql.Thunk(lambda: PostComment)))
    ]
)

PostComment = gql.ObjectType(
    name="PostComment",
    fields=[
        gql.Field(name="post", type=Post),
        gql.Field(name="id", type=gql.String),
        gql.Feld(name="comment", type=gql.String)
    ]
)

Query = gql.ObjectType(
    name="Query",
    fields=[
        gql.Field(
            name="getPostById",
            args=[gql.Argument(name="postId", type=gql.String)],
            type=Post
        )
    ]
)

schema = gql.Schema(types=[Post, PostComment, Query])
print(schema.gql())
```


This will output a valid GraphQL schema
```graphql

type Post  {
 id : String
name : String!
comments : [PostComment]
 }



type PostComment  {
 post : Post
id : String
comment : String
 }




```

 # Api
 ##  gql.Scalar

Scalar GraphQL types are defined with the following Scalar instances:
```
import dataall.gql as gql
gql.ID
gql.String
gql.Boolean
gql.Integer
gql.Number
gql.Date
gql.AWSDateTime
```


 ##  Type Modifiers

Types can be modified using gql Type modifiers.
Type modifiers can be applied for any valid GraphQL type, including scalar and ObjecType .

#### `gql.ArrayType(type)`
Defines an array from the provided type

```python
import dataall.base.api.gql as gql

gql.ArrayType(gql.String)  # will output [String]

Foo = gql.ObjectType(name="Foo", fields=[gql.Field(name="id", type=gql.String)])
gql.ArrayType(Foo)  # will output [Foo]

```



#### `gql.NonNullableType(type)`
Defines a required type from the provided type

```python
import dataall.base.api.gql as gql

gql.NonNullableType(gql.String)  # will output String!

```


##  gql.Field

`gql.Field` defines a GraphQL Field

### Methods

#### **constructor** `gql.Field(name, type, args, directives)`
- `name (String)` : name of the field
- `type(gql.Scalar, gql.TypeModifier,gql.ObjectType,gql.Thunk)`: the type of the field
- `args(list(gql.Argument))` **optional**:  A list of gql.Argument, defining GraphQL arguments
- `directives(list(gql.DirectiveArgs))` : A list of field Directive arguments

```python
import dataall.base.api.gql as gql

Child = gql.ObjectType(name="Child", fields=[gql.Field(name="id", type=gql.String)])
# A simple field
id = gql.Field(name="id", type=gql.NonNullableType(gql.String))
print(id.gql())  # id : String!

# A field with arguments
listChildren = gql.Field(
    name="listChildren",
    type=gql.ArrayType(Child),
    args=[gql.Argument(name="childName", type=gql.String)]
)  # listChildren(childName:String) : [Child]

# A field with directives

directiveField = gql.Field(
    name="directiveField",
    type=gql.String,
    directives=[gql.DirectiveArgs(name="required")]
)  # directiveField : String @required

```

#### `gql.Field.directive(name)`
Returns the `gql.DirectiveArgs` instance with the provided name, or `None` if the field does not have a directive with the provided name


#### `gql.Field.has_directive(name)`
Returns `True` if the field has a directive named `name`, or False if the field has no directive named `name`.

### Properties
- `type` : the Field type
- `name` : the Field name
- `args` : the Field argument list, defaults to []
- `directives` : the Field directive list, defaults to []

The
#### `gql.Field.gql(with_directive=True)`
Returns a gql representation of the field.

 ##  gql.ObjectType

 ##  gql.Thunk


 ##  gql.Thunk
