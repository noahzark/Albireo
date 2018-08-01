def row2dict(row, cls):
    """
    convert SQLAlchemy row data to python dictionary
    :param row: a SQLAlchemy row data, typically an instance of table object
    :return: dictionary represent the row data
    """
    # d = row.__dict__

    # d.pop('_sa_instance_state', None)

    # return d

    convert = {
        # "DATETIME": datetime.datetime.isoformat
    }

    d = dict()
    for col in cls.__table__.columns:
        if col.name.startswith('_'):
            continue
        v = getattr(row, col.name)
        current_type = str(col.type)
        if current_type in convert.keys() and v is not None:
            try:
                d[col.name] = convert[current_type](v)
            except:
                d[col.name] = "Error: Failed to convert using ", unicode(convert[col.type])
        elif v is not None:
            d[col.name] = v
    return d
