from odoo import models, fields

class CylinderMaterial(models.Model):
    _name = 'impsa.cylinder.material'
    _description = 'Catálogo de Materiales de Cilindros'
    _order = 'name'

    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(string="Activo", default=True)

    # Restricción SQL para evitar duplicados exactos
    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'El nombre debe ser único',
    )