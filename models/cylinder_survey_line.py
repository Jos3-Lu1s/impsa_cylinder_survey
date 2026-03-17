from odoo import models, fields, api
class CylinderSurveyLine(models.Model):
    _name = 'impsa.cylinder.survey.line'
    _description = 'Cylinder Survey Line'

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Survey",
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        "product.product",
        string="Descripción",
        domain="[('categ_id.name', '=', 'SELLOS')]"
    )

    description_label = fields.Char(
        string="Descripción",
        required=True,
        help="Escriba aquí o seleccione un producto"
    )

    code = fields.Char(string="Código", related="product_id.default_code", store=True)

    dimensions = fields.Char(string="Dimensiones")
    
    type_piece = fields.Selection([
        ('piston', 'Pistón'),
        ('head', 'Cabeza'),
        ('other', 'Otro'),
    ], string='Tipo de Pieza')
    
    material_drop = fields.Many2one(
        "impsa.cylinder.material",
        string="Material desplegable",
    )
    
    unit_cantity = fields.Integer(string="Cantidad")
    
    unit_total = fields.Integer(string="Total", compute="_compute_unit_total", store=True)
    
    @api.depends('unit_cantity', 'survey_id.cylinder_qty')
    def _compute_unit_total(self):
        for line in self:
            cylinders = line.survey_id.cylinder_qty or 0
            quantity = line.unit_cantity or 0
            line.unit_total = cylinders * quantity
            
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description_label = self.product_id.display_name
        