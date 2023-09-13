def DefaultResolver(field):
    def resolver(root, args, context):
        if root.get(field.name):
            return root[field.name]

    return resolver
