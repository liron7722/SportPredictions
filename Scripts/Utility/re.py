from re import finditer, findall


def get_prev_season_string(current_season):
    res = [str(int(x.group()) - 1) for x in finditer(r'\d+', current_season)]
    return '-'.join(res)


def get_int_from_string(txt):
    if type(txt) is int:
        return txt
    elif type(txt) is str:
        temp = findall('\d+', txt) if txt is not None else None
        return int(temp[0]) if len(temp) == 1 else None
    elif type(txt) is list:
        for i in range(len(txt)):
            txt[i] = get_int_from_string(txt[i])
        return txt

