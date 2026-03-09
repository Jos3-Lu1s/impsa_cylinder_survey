from odoo import models, fields

class CylinderImage(models.Model):
    _name = 'impsa.cylinder.image'
    _description = 'Imágenes del Cilindro'
    _order = 'sequence, id desc'

    survey_id = fields.Many2one(
        'impsa.cylinder.survey', 
        string='Levantamiento', 
        ondelete='cascade'
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Descripción", required=True)
    
    # Categorizar la foto para saber de qué pieza es
    component = fields.Selection([
        ('barrel', 'Camisa'),
        ('rod', 'Vastago'),
        ('piston', 'Piston'),
        ('head', 'Cabeza'),
        ('stroke', 'Carrera'),
    ], string="Componente", required=True)

    # max_width y max_height para proteger el servidor de fotos de 10MB
    image = fields.Image(string="Imagen", max_width=1920, max_height=1920, required=True)