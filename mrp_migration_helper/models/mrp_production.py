# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def onchange_producing(self):
        for production in self:
            _logger.warning(
                'Triggering onchange production for %s, %s', production, production.name)
            production._onchange_producing()
        return True
