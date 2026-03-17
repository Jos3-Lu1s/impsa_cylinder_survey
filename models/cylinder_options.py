from odoo import models, fields

class CylinderOptions(models.Model):
    _name = 'impsa.cylinder.options'
    _description = 'Catálogo de valores'

    name = fields.Char(string="Nombre", required=True)
    
    