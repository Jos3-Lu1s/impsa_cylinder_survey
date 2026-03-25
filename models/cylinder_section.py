from odoo import models, fields

class CylinderSection(models.Model):
    _name = 'impsa.cylinder.section'
    _description = 'Cylinder Section'

    survey_id = fields.Many2one(
        'impsa.cylinder.survey', 
        string='Survey', 
        required=True, 
        ondelete='cascade')
    
    sequence = fields.Integer(
        string="No. Camisa"
    )
    
    barrel_length = fields.Float(
        string="Longitud de la Camisa"
    ) 
    
    barrel_inner_diameter = fields.Float(
        string="Diámetro Interno"
    )
    
    barrel_outer_diameter = fields.Float(
        string="Diámetro Externo"
    )
    
    is_last = fields.Boolean(
        string="Es última sección"
    )