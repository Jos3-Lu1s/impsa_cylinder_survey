from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CylinderSurveyLine(models.Model):
    _name = 'impsa.cylinder.survey.line'
    _description = 'Línea de Levantamiento de Cilindros'

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento",
        ondelete='cascade',
        index=True
    )

    product_id = fields.Many2one(
        "product.product",
        string="Producto Base",
        domain="[('categ_id.name', '=', 'SELLOS')]",
        ondelete='restrict'
    )

    description_label = fields.Char(
        string="Descripción del Empaque",
        required=True,
        help="Nombre descriptivo del empaque o sello (ej. Sello de Vástago, O-Ring, Limpiador)."
    )
    
    code_label = fields.Char(
        string="Código Capturado",
        help="Código de referencia del fabricante o número de parte capturado del catálogo."
    )

    code = fields.Char(
        string="Código Maestro", 
        related="product_id.default_code", 
        store=True
    )

    dimensions = fields.Char(string="Dimensiones")
    
    type_piece = fields.Selection([
        ('piston', 'Émbolo'),
        ('head', 'Cabeza'),
        ('other', 'Otro'),
    ], string='Aplicación en Pieza')
    
    material_drop = fields.Many2one(
        "impsa.cylinder.material",
        string="Material",
        ondelete='restrict'
    )
    
    unit_quantity = fields.Integer(
        string="Cantidad por Cilindro", 
        default=1, 
        required=True,
        help="Número de piezas de este tipo que utiliza un solo cilindro."
    )
    
    unit_total = fields.Integer(
        string="Total a Pedir",
        compute="_compute_unit_total", 
        store=True,
        readonly=False,
        help="Total acumulado a solicitar. Se calcula automáticamente como (Cant. por Cilindro x Total de Cilindros), pero permite ajuste manual si se requiere un stock extra."
    )

    @api.constrains('unit_quantity')
    def _check_unit_quantity(self):
        for line in self:
            if line.unit_quantity <= 0:
                raise ValidationError(_("La cantidad por cilindro debe ser mayor a cero."))
    
    @api.depends('unit_quantity', 'survey_id.cylinder_qty')
    def _compute_unit_total(self):
        for line in self:
            cylinders = line.survey_id.cylinder_qty or 0
            quantity = line.unit_quantity or 0
            line.unit_total = cylinders * quantity
            
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.description_label = line.product_id.name
                line.code_label = line.product_id.default_code
            
    @api.onchange('code_label')
    def _onchange_code_label(self):
        for line in self:
            if line.code_label:
                product = self.env['product.product'].search([
                    ('default_code', '=ilike', line.code_label),
                    ('categ_id.name', '=', 'SELLOS')
                ], limit=1)

                if product:
                    line.product_id = product.id
                    line.description_label = product.name
                else:
                    # Si no existe, limpiamos el producto.
                    line.product_id = False