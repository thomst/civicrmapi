
def dict_to_where_clause_list(data):
    where_params = list()
    for key, value in data.items():
        where_params.append([key, '=', value])
    return where_params
