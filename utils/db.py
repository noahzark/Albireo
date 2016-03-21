def row2dict(row):
    '''
    convert SQLAlchemy row data to python dictionary
    :param row: a SQLAlchemy row data, typically an instance of table object
    :return: dictionary represent the row data
    '''
    d = row.__dict__

    d.pop('_sa_instance_state', None)

    return d