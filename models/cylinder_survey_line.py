from odoo import models, fields, api
class CylinderSurveyLine(models.Model):
    _name = 'impsa.cylinder.survey.line'
    _description = 'Cylinder Survey Line'

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Survey",
        ondelete='cascade'
    )

    description_springs = fields.Many2one(
        "product.product",
        string="Descripción",
        domain="[('categ_id.name', '=', 'Sellos')]"
    )

    code = fields.Char(string="Código", related="description_springs.default_code", store=True)

    dimensions = fields.Char(string="Dimensiones")
    type_piece = fields.Selection([
        ('enbolo', 'Énbolo'),
        ('head', 'Cabeza'),
        ('other', 'Otro'),
    ], string='Tipo de Pieza')
    
    unit_cantity = fields.Integer(string="Cantidad")
    
    unit_total = fields.Integer(string="Total", compute="_compute_unit_total", store=True)
    
