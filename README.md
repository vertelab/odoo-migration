# odoo-migration
Code for migrating database records from different odoo versions

1. Create a .odoorpcrc file with credentials to source and target databases in your home folder. It is the same file that stores OdooRPC credentials
```
[source]
type = ODOO
host = 192.168.1.OLD
protocol = jsonrpc
port = 8069
timeout = 120.0
user = admin
passwd = password
database = database_old

[target]
type = ODOO
host = localhost (if you want to use the helper modules, install this repo on the target machine)
protocol = jsonrpc
port = 8069
timeout = 120.0
user = admin
passwd = password
database = database_new
```
2. Open your favourite python interpreter and run 
```python
from configuration import *
```
3. Run migrate_model method like this:
```python
migrate_model(
    model='res.partner',
    domain=[('id', 'not in', list(range(1, 7)))], # exclude some partners
    mapping=dict(
        name='',
        type='',
    ), 
    before="""
print("run som code before creating/updating records")
    """,
    after="""
print("run som code after creating/updating records")
    """,
)
```