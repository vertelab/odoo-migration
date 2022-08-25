from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def compute_from_lines(self):
       self._compute_from_lines()
