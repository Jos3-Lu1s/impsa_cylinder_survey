from odoo import models, fields, api
from datetime import date

class HumanResourcesDepart(models.Model):
    _inherit = 'hr.department'

    hourly_cost=fields.Monetary(string="Costo por Hora", store=True, tracking=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency",string="Moneda",default=lambda self: self.env.company.currency_id)