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
    
    @api.depends('unit_cantity', 'survey_id.cylinder_qty')
    def _compute_unit_total(self):
        for line in self:
            cylinders = line.survey_id.cylinder_qty or 0
            quantity = line.unit_cantity or 0
            line.unit_total = cylinders * quantity
            
    @api.onchange('description_springs')
    def _onchange_description_springs(self):
        for line in self:
            if line.description_springs:
                line.dimensions = line.description_springs.name
                # line.type_piece = line.description_springs.product_tmpl_id.type_piece
    
