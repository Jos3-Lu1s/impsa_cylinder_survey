from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CylinderGroup(models.Model):
    _name = "impsa.cylinder.group"
    _description = "Grupo de Cilindros"

    survey_id = fields.Many2one(
        "impsa.cylinder.survey", 
        string="Levantamiento", 
        required=True, 
        ondelete="cascade",
        index=True
    )

    name = fields.Char(
        string="Identificador del Grupo", 
        required=True, 
        placeholder="Ej. 3 Cilindros Idénticos del frente..."
    )
    
    quantity = fields.Integer(
        string="Cantidad", 
        required=True, 
        default=1,
        help="¿Cuántos cilindros de este levantamiento comparten estas mismas operaciones?"
    )

    operational_record_ids = fields.One2many(
        "impsa.operational.record.line", 
        "group_id",
        string="Registro Operativo",
    )

    group_total_hours = fields.Float(
        string="Subtotal de Horas",
        compute="_compute_group_total_hours",
        store=True,
        help="Tiempo total estimado para este grupo (Suma de horas de sus operaciones multiplicada por la cantidad de cilindros)."
    )

    image_ids = fields.One2many(
        'impsa.cylinder.image', 
        'group_id', 
        string="Imágenes por Cilindro",
    )

    @api.depends('operational_record_ids.hr', 'quantity')
    def _compute_group_total_hours(self):
        for group in self:
            base_hours = sum(group.operational_record_ids.mapped('hr'))
            group.group_total_hours = base_hours * group.quantity

    @api.constrains('quantity')
    def _check_group_quantity(self):
        for group in self:
            if group.quantity < 1:
                raise ValidationError(_("Un grupo debe contener al menos 1 cilindro."))