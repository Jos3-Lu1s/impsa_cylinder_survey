from odoo import models, fields, api

class ImpsaCylinder(models.Model):
    _name = "impsa.cylinder"
    _description = "Cilindro Físico"
    _order = "sequence, id"

    name = fields.Char(string="Identificador", required=True, default="Nuevo Cilindro")
    sequence = fields.Integer(string="Secuencia", default=10)
    
    group_id = fields.Many2one(
        "impsa.cylinder.group", 
        string="Grupo al que pertenece", 
        required=True, 
        ondelete="cascade",
        index=True
    )
    
    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento",
        related="group_id.survey_id",
        store=True,
        index=True
    )

    image_ids = fields.One2many(
        "impsa.cylinder.image",
        "cylinder_id",
        string="Imágenes del Cilindro"
    )
    
    notes = fields.Text(string="Observaciones Específicas")