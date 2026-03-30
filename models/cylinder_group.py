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
    sale_order_id = fields.Many2one(
        'sale.order',
        string="Cotización"
    )

    sale_state = fields.Selection(
        related='sale_order_id.state',
        string="Estado",
        store=True
    )

    @api.constrains('quantity')
    def _check_group_quantity(self):
        for group in self:
            if group.quantity < 1:
                raise ValidationError(_("Un grupo debe contener al menos 1 cilindro."))
                
    def action_open_sale_order(self):
        self.ensure_one()
        
        if self.sale_order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Orden de Venta',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': self.sale_order_id.id,
                'target': 'current',
            }