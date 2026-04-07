from odoo import models, fields, api, _
from datetime import date

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    code_partner = fields.Char(string="Codigo de contacto",store=True)