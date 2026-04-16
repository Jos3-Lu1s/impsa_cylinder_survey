from odoo import models, fields

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    contacto_id = fields.Many2one(
        'res.partner',
        string='Contacto',
    )