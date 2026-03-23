from odoo import models, fields

class CylinderOptions(models.Model):
    _name = 'impsa.cylinder.options'
    _description = 'Catálogo de valores'
    _order = 'name'

    name = fields.Char(string="Nombre", required=True)
    
    code = fields.Char(
        string="Código Técnico", 
        required=True, 
        copy=False, 
        help="Código único para la lógica de la interfaz:\n" 
        "- Doble efecto (CE-DE)\n"
        "- Simple efecto (CE-SE)\n"
        "- Telescópico (CE-T)\n"
        "- Doble vástago (CE-DV)\n"
        "- Otros (CE-OT)"
    )

    active = fields.Boolean(string="Activo", default=True)

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Ya existe una opción con este nombre.',
    )
    
    _code_unique = models.Constraint(
        'UNIQUE(code)',
        '¡El código técnico debe ser único!',
    )