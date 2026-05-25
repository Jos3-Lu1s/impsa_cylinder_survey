from odoo import models, fields


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    branch_code = fields.Char(
        string="Código de Sucursal",
        help="Código identificador de la sucursal bancaria."
    )