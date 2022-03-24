def udf(spark, ref):
    print('hello from udf')
    source = ref('rawdatainput')
    print('got source ', source)
