# odoo-migration
Code for migrating database records from different odoo versions

1. Create a .odoorpcrc file with credentials to source and target databases
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