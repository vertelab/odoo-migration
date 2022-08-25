# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def onchange_currency(self):
        for invoice in self:
            _logger.warning("Triggering onchange currency for %s, %s", invoice, invoice.name)
            invoice._onchange_currency()
        return True

    def recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        for invoice in self:
            _logger.warning("Recomputing dynamic lines for %s, %s", invoice, invoice.name)
            invoice._recompute_dynamic_lines(recompute_all_taxes, recompute_tax_base_amount)
        return True

    def message_post_with_view_rpc(self, views_or_xmlid, **kwargs):
        if (values := kwargs.get('values', None) or dict()):
            if values['self'] == self.id:
                values['self'] = self
            if (origin :=values['origin']):
                model = origin.split('(')[0]
                ids = eval(origin.split(model)[-1])
                values['origin'] = self.env[model].browse(ids)
        kwargs['values'] = values
        if values.get('origin'):
            super().message_post_with_view(views_or_xmlid, **kwargs)
        else:
            _logger.error(f"{origin=}")
        return True
