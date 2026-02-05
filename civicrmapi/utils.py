
def dict_to_where_clause_list(data):
    where_params = list()
    for key, value in data.items():
        where_params.append([key, '=', value])
    return where_params


def format_requests_response(value):
    msg = f'URL: {value.url}\n'
    msg += f'STATUS: {value.status_code}\n'
    msg += f'CONTENT: {value.text}\n'
    return msg


def format_subprocess_response(value):
    msg = f'RETURN CODE: {value.returncode}\n'
    if value.stdout:
        msg += f'STDOUT: {value.stdout}\n'
    if value.stderr:
        msg += f'STDERR: {value.stderr}\n'
    return msg
