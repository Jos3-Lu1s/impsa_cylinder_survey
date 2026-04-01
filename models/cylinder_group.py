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

    image_ids = fields.One2many(
        'impsa.cylinder.image', 
        'group_id', 
        string="Imágenes por Cilindro",
    )

    ''' ------------------------
        SALE FIELDS RELATED
    -------------------------'''
    apu_id = fields.Many2one(
        'impsa.apu.survey',
        string="Análisis de Precio (APU)",
        readonly=True,
        help="APU generado para este grupo de cilindros."
    )

    apu_state = fields.Selection(
        related='apu_id.state',
        string="Estado APU",
        store=True
    )

    @api.constrains('quantity')
    def _check_group_quantity(self):
        for group in self:
            if group.quantity < 1:
                raise ValidationError(_("Un grupo debe contener al menos 1 cilindro."))
                
    def action_open_apu(self):
        """Abre el APU relacionado a este grupo desde la vista del levantamiento"""
        self.ensure_one()
        if self.apu_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Análisis de Precio Unitario',
                'res_model': 'impsa.apu.survey',
                'view_mode': 'form',
                'res_id': self.apu_id.id,
                'target': 'current',
            }