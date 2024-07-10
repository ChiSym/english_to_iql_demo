def run_query(parser, interpreter, query):
    tree = parser.parse(query)
    df = interpreter.transform(tree)

    # currently getting some nulls, will investigate 
    return df.drop_nulls()