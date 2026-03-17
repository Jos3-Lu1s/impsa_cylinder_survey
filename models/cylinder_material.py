from odoo import models, fields

class CylinderMaterial(models.Model):
    _name = 'impsa.cylinder.material'
    _description = 'Materiales de Cilindros'

    name = fields.Char(string="Nombre", required=True)