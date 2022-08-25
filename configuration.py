import json
from pprint import pprint

from colorcodes import Colorcodes

try:
    import odoorpc
except ImportError:
    raise Warning(
        'odoorpc library missing. Please install the library. Eg: pip3 install odoorpc')

color = Colorcodes()
p = color.print_colors

IMPORT = '__import__'

source = odoorpc.ODOO.load('source')
source.__name__ = 'source'
source.env.context.update({'active_test': False})
p(color="green_bg", text=f"source.version = {source.version}")
p(color="green_fg", text=f"source.env     = {source.env}")

target = odoorpc.ODOO.load('target')
target.__name__ = 'target'
target.env.context.update({
    'mail_create_nolog': True,
    'mail_create_nosubscribe': True,
    'mail_notrack': True,
    'tracking_disable': True,
    'tz': 'UTC',
})
p(color="green_bg", text=f"target.version = {target.version}")
p(color="green_fg", text=f"target.env     = {target.env}")

for server in ['ir.mail_server', 'fetchmail.server']:
    if target.env[server].search([]):
        raise Warning(f"Active {server}")

target.env.context.update({'active_test': False})

def browse(conn, model, domain):
    ids = conn.env[model].search(domain)
    return conn.env[model].browse(ids)


def get_res_id_from_conn(conn, domain=None, xmlid=None):
    if xmlid:
        res = conn.env['ir.model.data'].search_read([
            ('module', '=', xmlid.split('.')[0]),
            ('name', '=', xmlid.split('.')[1]),
        ], ['res_id'], limit=1)
        return res[0]['res_id'] if res else 0
    elif domain:
        return conn.env['ir.model.data'].search_read(domain)


def map_records_manually(source_model, target_model=None, source_field=None, target_field=None, mapping=None):
    s = source.env[source_model]
    t = target.env[target_model or source_model]
    source_field = source_field or 'id'
    target_field = target_field or source_field
    s_reads = s.search_read([], [source_field], order='id')
    t_reads = t.search_read([], [target_field], order='id')
    for s_id, t_id in mapping.items():
        print(next(filter(lambda read: read['id'] == s_id, s_reads))[
              source_field])
        target_id = next(filter(lambda read: read['id'] == t_id, t_reads))
        print(target_id[target_field])
        xmlid = get_xmlid(source_model, s_id)
        if get_res_id_from_conn(target, xmlid=xmlid) == target_id['id']:
            print(f"{xmlid} exists already...")
        elif input('Map records?').lower() == 'y':
            create_xmlid(t._name, res_id=t_id, xmlid=xmlid)


def map_existing_records(source_model, target_model=None, source_field=None, target_field=None):
    s = source.env[source_model]
    t = target.env[target_model or source_model]
    s_reads = s.search_read([], [source_field or 'id'], order='id')
    t_reads = t.search_read(
        [], [target_field or source_field or 'id'], order='id')
    metadatas = s.get_metadata([r['id'] for r in s_reads])
    for read in s_reads:
        metadata = next(
            filter(lambda meta: meta['id'] == read['id'], metadatas))
        import_xmlid = get_xmlid(source_model, read['id'])
        xmlid = metadata['xmlid']
        if not (res_id := get_res_id_from_conn(target, xmlid=xmlid)):
            if source_field or target_field:
                s_value = read[source_field]
                res_ids = list(
                    filter(lambda r: r[target_field or source_field] == s_value, t_reads))
                print(res_ids)
                if len(res_ids) == 1:
                    res_id = res_ids[0]['id']
        if res_id and not get_res_id_from_conn(target, xmlid=import_xmlid):
            create_xmlid(target_model or source_model,
                         xmlid=import_xmlid, res_id=res_id)


def print_xmlids(conn, model, field=None, active_test=False, limit=0):
    reads = conn.env[model].with_context(active_test=active_test).search_read([], [
        field or 'id'], limit=limit, order='id')
    metadatas = conn.env[model].with_context(
        active_test=active_test).get_metadata([read['id'] for read in reads])
    for read in reads:
        metadata = next(filter(lambda r: r['id'] == read['id'], metadatas))
        print(f"{metadata['id']}{' '*(3-len(str(metadata['id'])))}"
              f"{metadata['xmlid']}{' '*(45-len(str(metadata['xmlid'])))}"
              f"{read[field or 'id']}")


def create_xmlid(model, xmlid, res_id):
    _model = 'ir.model.data'
    module = xmlid.split('.')[0]
    vals = dict(module=module,
                name=xmlid.split('.')[1],
                noupdate=module != IMPORT,
                res_id=res_id)
    if isinstance(model, odoorpc.models.MetaModel):
        vals['model'] = model._name
        model = model.env[_model]
    else:
        vals['model'] = model
        model = target.env[_model]
    _name = model.__name__.upper()

    try:
        res = model.create(vals)
    except:
        p(f"{_name}: XML_ID: {xmlid} | CREATE: FAIL!", 'red_bg', end='')
        p(f"Should not happen...Did you call this method manually? {vals}", 'red_fg')
    else:
        p(f"{_name}: XML_ID: {xmlid} | CREATE: SUCCESS!", 'green_bg')
        return model.read(res)


def get_xmlid(name, ext_id, module=IMPORT):
    return f"{module}.{name.replace('.', '_')}_{ext_id}"


def migrate_model(model, **params):
    """
    Use this method for migrating model from source to target
    - Example: migrate_model('res.partner')
    - Keyworded arguments default values:

    Parameters
        - model (str) - Model to migrate records from source to target
        - **params : keyworded arguments
            - calc    (dict) - Runs code on specific fields, default {}
            - context (dict) - Sets context to source and target, default {}
            - create  (bool) - Creates records, set to False to update records, default True
            - custom  (dict) - Updates vals before create/write, default {}
            - debug   (bool) - Shows debug messages, default False
            - domain  (list) - Migrate records that matches search criteria, i.e [('name','=','My Company')], default []
            - diff    (dict) - If field names don't match in source and target i.e {'image':'image_1920'}, default {}
            - exclude (list) - Excludes certain fields in source i.e ['email_formatted'], default []
            - ids     (list) - Provide your own record ids to migrate i.e [1,3], default []
            - include (list) - Provide your own list of fields names to migrate ['name','email'], default []
            - model2  (str)  - Migrate records to another model, default same as model

    Returns
        - vals (dict) if create/write fails
        - id   (int)  if create succeeds
    """
    def compare_values(record, model_fields, vals):
        input(f"{record=}") if debug else None
        for key in list(vals):
            if not (field := model_fields.get(key)):
                raise KeyError(f"Key not found '{key}'")
            field_type = field.get('type')
            if key in record:
                value = record[key]
                if field_type in ['many2one']:
                    if isinstance(value, list) and len(value) == 2:
                        value = value[0]
                elif field_type in ['one2many', 'many2many']:
                    if isinstance(value, list):
                        for command in vals[key]:
                            if isinstance(command, (list, tuple)):
                                if command[0] == 4 and command[1] in value:
                                    vals.pop(key)
                                if command[0] == 6 and set(command[2]) == set(value):
                                    vals.pop(key)
                # elif field_type in ['binary']:
                #     binary = vals[key]
                #     if binary and '\n' in binary:
                #         vals[key] = binary.replace('\n', '')
                if value == vals.get(key):
                    vals.pop(key)
        return vals

    def compress_dict(dictionary, sep="\n"):
        if isinstance(dictionary, dict):
            return sep.join([f"{k}: {str(v)[:50] + '...' if len(str(v)) > 50 else v}" for k, v in dictionary.items()])

    def migrate_record(model, vals, xmlid):
        _vals = None

        def print_info(msg):
            print(f"{params.keys()=}")
            input(f"{msg}: {model=}, {vals=}, {xmlid=}")

        if 'skip' in vals:
            if sync and debug:
                print_info('skip')
            return 0

        if (res_id := search(model, xmlid=xmlid)):
            if (record := read(model, fields=vals, res_id=res_id)):
                vals = compare_values(record, fields_get(model), vals)
                if vals and not debug:
                    model.write(res_id, vals)
                    p('UPDATE', 'yellow_bg', end=' ')
                    p(f"{model._name}\n"
                      f"vals={compress_dict(vals)}\n"
                      f"[ID={res_id}, {xmlid=}])",
                      'yellow_fg')
            else:
                p('UPDATE', 'red_bg', end=' ')
                p(f"Record not found, {record=}, you need to update or "
                  f"vals={compress_dict(vals)}",
                  'red_fg')

        elif sync and not debug:
            res_id = model.create(vals)
            data_id = create_xmlid(model, xmlid, res_id)[0]
            search(model).append(dict(id=data_id['id'],
                                      complete_name=data_id['complete_name'],
                                      res_id=data_id['res_id']))
        
            p('CREATE', 'green_bg')
            p(f"{model._name}\nvals={compress_dict(vals)}\n[ID={res_id}, {xmlid=}])", 'green_fg')

        if vals:
            params['counter'] += 1
        print_info('debug') if debug else None
        return res_id

    def dot2u(text):
        return str(text).replace('.', '_')

    def args2key(*args):
        return '_'.join([dot2u(arg.__name__ if hasattr(arg, '__name__') else str(arg)) for arg in args])

    def fields_get(model):
        key = args2key(model._odoo, model, fields_get)
        if key not in params:
            params[key] = model.fields_get()
            p(f"params['{key}'] ({len(params[key])} fields)", "tg")
        return params[key]

    def find(model, field, value, fields=[]):
        def get(record):
            if (fields_get(model)[field]['type'] == 'many2one' and isinstance(record[field], list)):
                return record[field][0] == value
            return record[field] == value
        key = args2key(model._odoo, model, find, field, value)
        if key not in params:
            params[key] = {}
        if value in (param := params[key]):
            return param[value]
        reads = read(model, fields)
        if (found := next(filter(get, reads), [])):
            param[value] = found
        return found or []

    def read(model, fields=None, res_id=None):
        def get(record):
            return record['id'] == res_id
        key = args2key(model._odoo, model, read)
        if key not in params:
            params[key] = model.search_read([], fields or [])
            p(f"params['{key}'] ({len(params[key])} records)", "tg")
        param = params[key]
        if res_id:
            return next(filter(get, param), 0)
        return param

    def search(model, res_id=None, xmlid=None):
        def get(record):
            return record['res_id'] == res_id if res_id else record['complete_name'] == xmlid
        key = args2key(model._odoo, model, search)
        if key not in params:
            params[key] = model.env['ir.model.data'].search_read(
                [('model', '=', model._name)], ['complete_name', 'res_id'])
            p(f"params['{key}'] ({len(params[key])} records)", "tg")
        param = params[key]
        if res_id:
            return next(filter(get, param), {}).get('complete_name', 0)
        if xmlid:
            return next(filter(get, param), {}).get('res_id', 0)
        return param

    def get_source_reads(model, fields):
        source_model_reads = f"source_{model.replace('.', '_')}_reads"
        if source_model_reads not in params:
            params[source_model_reads] = (
                {record['id']: {field: record[field] for field in fields}
                 for record in source.env[model].search_read([], fields)})
            print(f"Added '{source_model_reads}'")
        return params[source_model_reads]

    def get_res_id(xmlid):
        if xmlid not in params:
            params[xmlid] = {}
        param = params.get(xmlid)
        if not (res_id := param.get('res_id', 0)):
            res_id = get_res_id_from_conn(target, xmlid=xmlid)
            if not res_id and 'model' in params[xmlid]:
                res_id = migrate_record(
                    param['model'], param['vals'], xmlid)
            if res_id:
                param['res_id'] = res_id
                p(f"params[{xmlid}] = {res_id}", "tg")
        return res_id

    def get_res_ids(model):
        model_res_ids = f"{model.replace('.', '_')}_res_ids"
        if model_res_ids not in params:
            ids = source.env[model].search([], order='id')
            search_reads = get_res_id_from_conn(source, domain=[
                ('model', '=', model),
                ('res_id', 'in', ids)])
            params[model_res_ids] = {
                x['res_id']: x['complete_name'] for x in search_reads}
            print(f"Added '{model_res_ids}'")
        return params[model_res_ids]

    def get_search_read(model, key, domain=[]):
        search_read = f"{model.replace('.', '_')}_search_read"
        if search_read not in params:
            params[search_read] = {
                x[key]: x['id']
                for x in target.env[model].search_read(domain, [key])}
            print(f"Added '{search_read}'")
        return params[search_read]

    def vals_builder(data):
        vals = {}
        for tkey, skey in mapping.items():
            if not skey:
                skey = tkey
            if skey in source_fields_get:
                value = data[skey]
                field_type = source_fields_get[skey]['type']
                input(f"{skey=}, {field_type=}, {value=}") if debug else None
                if 'relation' in source_fields_get[skey]:
                    s_model = source_fields_get[skey]['relation']
                    t_model = target_fields_get[tkey]['relation']
                    source_relation = source.env[s_model]
                    target_relation = target.env[t_model]
                    input(
                        f"{source_relation} => {target_relation}") if debug else None
                    if field_type in ['many2one']:
                        if isinstance(value, list) and len(value) == 2:
                            val = value[0]
                            value_xmlid = get_xmlid(s_model, val)
                            if not (value := search(target_relation, xmlid=value_xmlid)):
                                value_xmlid = search(
                                    source_relation, res_id=val)
                                value = search(target_relation,
                                               xmlid=value_xmlid)

                    elif field_type in ['one2many', 'many2many'] and value:
                        value_list = []
                        for val in value:
                            val_xmlid = get_xmlid(s_model, val)
                            if not (value_id := search(target_relation, xmlid=val_xmlid)):
                                val_xmlid = search(source_relation, res_id=val)
                                value_id = search(
                                    target_relation, xmlid=val_xmlid)
                            if value_id:
                                value_list.append(value_id)
                        value = [(6, 0, value_list)] if value_list else False

                elif field_type in ['binary']:
                    vals[tkey] = value
                    binary = vals[tkey]
                    if binary and '\n' in binary:
                        vals[tkey] = binary.replace('\n', '')

                vals[tkey] = value
                input(f"{value=}") if debug else None
            else:
                print(
                    f"{skey} not found in source.env['{model}']") if debug else None
        input(f"{vals=}") if debug else None
        return vals

    after = params.pop('after', '')
    before = params.pop('before', '')
    context = params.pop('context', {})
    debug = params.get('debug', False)
    domain = params.get('domain', [])
    mapping = params.get('mapping', {})
    target_fields = params.get('target_fields', [])
    source_fields = params.get('source_fields', [])
    model2 = params.get('model2', model)
    reads = params.get('reads', [])
    offset = params.get('offset', 0)
    limit = params.get('limit', 0)
    sync = params.get('sync', True)

    source_model = source.env[model]
    target_model = target.env[model2]

    source_fields_get = fields_get(source_model)
    target_fields_get = fields_get(target_model)
    params['counter'] = 0
    if context:
        target.env.context.update(context)
# MAIN LOOP
    source_reads = source_model.search_read(
        domain, source_fields + [v if v else k for k, v in mapping.items()], limit=limit, offset=offset, order='id')

    # search(model2)
    # read(model2, sorted(target_fields + list(mapping)))
    # for source_id in source_ids:
    errors = []
    for data in source_reads:
        xmlid = get_xmlid(model, data['id'])
        vals = vals_builder(data)
        input(f"{before=}\n{after=}") if debug else None
        try:
            exec(before)
            res = migrate_record(target_model, vals, xmlid)
            exec(after)
        except Exception as e:
            print(f"{e=}")
            errors.append(f"vals={compress_dict(vals)}, {xmlid=}")

    p(f"Done migrating {model}!", 'green_bg')
    return errors if errors else f"No errors ({limit=}, {offset=})"

p('Methods loaded', 'green_fg')