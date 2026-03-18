from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CylinderGroup(models.Model):
    _name = "impsa.cylinder.group"
    _description = "Grupo de Cilindros"

    survey_id = fields.Many2one(
        "impsa.cylinder.survey", 
        string="Levantamiento", 
        required=True, 
        ondelete="cascade" # Crítico: Si se borra el levantamiento, se borran los grupos
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
        "operational.record.line", 
        "group_id",
        string="Registro Operativo",
    )

    @api.constrains('quantity')
    def _check_group_quantity(self):
        for group in self:
            if group.quantity < 1:
                raise ValidationError("Un grupo debe contener al menos 1 cilindro.")