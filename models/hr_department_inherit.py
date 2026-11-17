<<<<<<< HEAD
from odoo import models, fields, api
from datetime import date

class HumanResourcesDepart(models.Model):
    _inherit = 'hr.department'

    hourly_cost=fields.Monetary(string="Costo por Hora", store=True, tracking=True, currency_field="currency_id")
=======
from odoo import models, fields, api
from datetime import date

class HumanResourcesDepart(models.Model):
    _inherit = 'hr.department'

    hourly_cost=fields.Monetary(string="Costo por Hora", store=True, tracking=True, currency_field="currency_id")
>>>>>>> 1a391fe80b61aba2c9b6270a7d8b0625aac85b09
    currency_id = fields.Many2one("res.currency",string="Moneda",default=lambda self: self.env.company.currency_id)