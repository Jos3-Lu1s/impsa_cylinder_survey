from odoo import models, fields

class CylinderOptions(models.Model):
    _name = 'impsa.cylinder.options'
    _description = 'Catálogo de valores'
    _order = 'name'

    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(string="Activo", default=True)

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'El nombre debe ser único',
    )