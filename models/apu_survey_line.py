from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class SaleOrderLM(models.Model):
    _name='impsa.apu.survey.line'
    _description='Lista de Materiales de Cotización'
    #CAMPOS RELACIONALES#
    currency_id = fields.Many2one("res.currency",string="Moneda",default=lambda self: self.env.company.currency_id)
    apu_id = fields.Many2one('impsa.apu.survey',string='Cotización',ondelete='cascade')
    product_id=fields.Many2one('product.template',string='Material')

    #CAMPOS DEL COTIZADOR DE MATERIALES#
    mo_hrs_lm = fields.Float(string="Tiempo MO",digits=(16, 2))
    unidad_lm = fields.Many2one('uom.uom',string='Unidad',)
    precio_unitario_lm = fields.Float(string='Precio Unitario',store=True)
    cantidad_lm = fields.Float(string="Cantidad", default=1.0)
    importe_material_lm = fields.Monetary(string="Imp. Material", compute='_compute_importe_material', store=True,currency_field="currency_id")
    importe_mo_lm = fields.Monetary(string="Imp. MO", compute='_compute_importe_mo', currency_field="currency_id")
    empleado_mo_lm = fields.Many2one('hr.department',string="Área")
    reference = fields.Text(
        string="Referencia",
        store=True
    )
    #MÉTODOS PARA EL COMPORTAMIENTO DINÁMICO DEL COTIZADOR#
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unidad_lm = self.product_id.uom_id
            self.precio_unitario_lm = self.product_id.list_price

    @api.depends('cantidad_lm','precio_unitario_lm')
    def _compute_importe_material(self):
        for line in self:
            line.importe_material_lm = line.cantidad_lm * line.precio_unitario_lm
            if line.unidad_lm.id == 4:
                line.mo_hrs_lm= line.cantidad_lm

    @api.depends('mo_hrs_lm','apu_id.costo_fijo_lm','apu_id.tipo_costo_mo','empleado_mo_lm.hourly_cost')
    def _compute_importe_mo(self):
        for line in self:
            if line.apu_id.tipo_costo_mo == 'costo_fijo_mo':
                line.importe_mo_lm=line.mo_hrs_lm*line.apu_id.costo_fijo_lm
                if line.unidad_lm.id == 4:
                    line.cantidad_lm=line.mo_hrs_lm
            elif line.apu_id.tipo_costo_mo == 'costo_empleado_mo':
                line.importe_mo_lm=line.mo_hrs_lm*line.empleado_mo_lm.hourly_cost
                if line.unidad_lm.id == 4:
                    line.cantidad_lm=line.mo_hrs_lm
            else:
                 line.importe_mo_lm=0
                 if line.unidad_lm.id == 4:
                    line.cantidad_lm=line.mo_hrs_lm
            
    """ @api.onchange('cantidad_lm')
    def _onchange_cantidad_lm(self):
        for record in self:
            if record.apu_id.cylinder_qty_by_group > 0:            
                record.cantidad_lm=(record.cantidad_lm*1)*record.apu_id.cylinder_qty_by_group """



