# odoo19/addons/modules/impsa_cylinder_survey/models/cylinder_section.py

from odoo import models, fields

class CylinderSection(models.Model):
    _name = 'impsa.cylinder.section'
    _description = 'Sección de Cilindro Telescópico'
    _order = 'sequence, id'

    survey_id = fields.Many2one(
        'impsa.cylinder.survey', 
        string='Levantamiento', 
        required=True, 
        ondelete='cascade'
    )
    
    sequence = fields.Integer(string="Secuencia", default=10)
    
    name = fields.Char(
        string="Descripción", 
        required=True,
        help="Ej: Camisa Principal, Primera Extensión, etc."
    )
    
    section_type = fields.Selection([
        ('main', 'Camisa Principal'),
        ('intermediate', 'Extensión Intermedia'),
        ('last', 'Última Extensión')
    ], string="Tipo de Sección", required=True)

    # ----------------------------------------------------
    # Dimensiones Generales
    # ----------------------------------------------------
    inner_diameter = fields.Float(
        string="Ø Interior", 
        required=True,
        help="Aplica para Camisa Principal y Extensiones Intermedias."
    )
    outer_diameter = fields.Float(
        string="Ø Exterior (Vástago)", 
        required=True,
        help="Todas las secciones tienen un diámetro exterior/vástago."
    )
    length = fields.Float(
        string="Longitud", 
        required=True,
        help="Todas las secciones tienen longitud."
    )

    # ----------------------------------------------------
    # Dimensiones del Émbolo
    # ----------------------------------------------------
    piston_diameter = fields.Float(
        string="Ø Émbolo", 
        required=True,
        help="No aplica en la camisa principal."
    )
    piston_length = fields.Float(
        required=True,
        string="Longitud de Émbolo"
    )

    # ----------------------------------------------------
    # Dimensiones de la Cabeza
    # ----------------------------------------------------
    head_diameter = fields.Float(
        string="Ø Cabeza", 
        required=True,
        help="No aplica en la última extensión."
    )
    head_length = fields.Float(
        required=True,
        string="Longitud de Cabeza"
    )