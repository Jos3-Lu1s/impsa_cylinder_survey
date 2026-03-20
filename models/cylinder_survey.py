from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class CylinderSurvey(models.Model):
    _name = "impsa.cylinder.survey"
    _description = "Levantamiento de Cilindros (F-05-01)"

    # Heredar de mail.thread y mail.activity.mixin
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Referencia", required=True, copy=False, readonly=True, default="Nuevo"
    )

    partner_id = fields.Many2one(
        "res.partner", string="Cliente", required=True, tracking=True
    )

    cylinder_qty = fields.Integer(
        string="Cantidad", 
        default=1, 
        required=True, 
        tracking=True,
        help="Número de cilindros que comparten exactamente estas mismas características."
    )

    allocated_qty = fields.Integer(
        string="Cilindros Asignados",
        compute="_compute_allocated_qty",
        store=True,
        help="Suma de los cilindros ya distribuidos en grupos."
    )

    group_ids = fields.One2many(
        "impsa.cylinder.group", 
        "survey_id",
        string="Grupos de Cilindros",
    )

    all_operational_record_ids = fields.One2many(
        "operational.record.line",
        "survey_id",
        string="Resumen de Operaciones",
        help="Vista consolidada de todas las operaciones de todos los grupos."
    )

    image_ids = fields.One2many(
        'impsa.cylinder.image', 
        'survey_id', 
        string="Galería de Imágenes"
    )

    # Camisa (Barrel)
    barrel_inner_diameter = fields.Float(string='Ø Interior')
    barrel_outer_diameter = fields.Float(string='Ø Exterior')
    barrel_length = fields.Float(string='Longitud')
    barrel_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes de la Camisa", 
        domain=[('component', '=', 'barrel')]
    )

    # Vástago (Rod)
    diameter_rod = fields.Float(string="Ø Vástago")
    rod_length = fields.Float(string='Longitud de Vástago')
    rod_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes del Vástago", 
        domain=[('component', '=', 'rod')]
    )
    
    diameter_rod2 = fields.Float(string="Ø Vástago 2")
    rod_length2 = fields.Float(string='Longitud de Vástago 2')

    # Émbolo (Piston)
    piston_diameter = fields.Float(string='Ø Émbolo') 
    piston_length = fields.Float(string='Longitud de Émbolo')
    piston_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes del Émbolo", 
        domain=[('component', '=', 'piston')]
    )

    # Cabeza (Head)
    head_diameter = fields.Float(string='Ø Cabeza')
    head_length = fields.Float(string='Longitud de Cabeza')
    head_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes de la Cabeza", 
        domain=[('component', '=', 'head')]
    )

    # Carrera (Stroke)
    stroke_length = fields.Float(string='Longitud de Carrera')
    stroke_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes del Ensamble", 
        domain=[('component', '=', 'stroke')]
    )
    
    # Accesorios
    accessories  = fields.Text(string='Accesorios')
    accessory_image_ids  = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes de accesorios", 
        domain=[('component', '=', 'accessory')]
    )

    date = fields.Date(string="Fecha", default=fields.Date.context_today)
    description = fields.Text(string="Descripción")
    cylinder_type = fields.Char(string="Cilindro de")
    identification_marks = fields.Char(
        string="Identificación", 
        help="Marcas, características o notas visuales para identificar el cilindro físicamente.",
        tracking=True
    )

    product_id = fields.Char(string="Descripción")
    code = fields.Char(string="Código")
    dimensions = fields.Char(string="Dimensiones")
    type_piece = fields.Selection([
        ('enbolo', 'Énbolo'),
        ('head', 'Cabeza'),
        ('other', 'Otro'),
    ], string='Tipo de Pieza')

    rotula_id = fields.Many2one(
        "product.product",
        string="Rotula",
        domain="[('categ_id.name', '=', 'FERRETERIA')]"
    )
    
    date_delivery = fields.Date(string="Fecha de Entrega")

    internal_notes = fields.Html(
        string="Notas Internas",
        help="Espacio para notas detalladas sobre este registro.",
    )

    cylinder_survey_line_ids = fields.One2many(
        "impsa.cylinder.survey.line",
        "survey_id",
        string="Empaques",
    )
    
    cylinder_to = fields.Many2one(
        "impsa.cylinder.options",
        string="Cilindro de",
    )

    total_tasks = fields.Integer(
        string='Total de Tareas',
        compute='_compute_operational_totals',
        store=True,
        help="Suma total de líneas en el registro operativo.",
        readonly=True
    )
    total_hours = fields.Float(
        string='Total de Horas',
        compute='_compute_operational_totals',
        store=True,
        help="Suma total de horas de todas las tareas.",
        readonly=True
    )
    state = fields.Selection([
        ('draft', 'Levantamiento'),
        ('quoted', 'Cotización'),
        ('confirmed', 'Orden de Trabajo'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True, copy=False)

    cylinder_type = fields.Selection([
        ('hydraulic', 'Hidráulico'),
        ('pneumatic', 'Neumático')
    ],string='Tipo de Cilindro')

    is_standardized = fields.Boolean(
        string='Normalizado'
    )

    ''' ------------------------
        Botones inteligentes
    -------------------------'''
    
    purchase_order_ids = fields.One2many(
        "purchase.order",
        "survey_id",
        string="Órdenes de Compra"
    )

    purchase_order_count = fields.Integer(
        compute="_compute_purchase_order_count"
    )

    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)

    def action_view_purchase_orders(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de Compra',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('survey_id', '=', self.id)],
        }

    lead_id = fields.Many2one(
        'crm.lead',
        string="Oportunidad"
    )

    lead_count = fields.Integer(
        string="Oportunidades",
        compute="_compute_lead_count"
    )

    def _compute_lead_count(self):
        for rec in self:
            rec.lead_count = 1 if rec.lead_id else 0

    def action_view_lead(self):
        self.ensure_one()
        
        if self.lead_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Oportunidad',
                'res_model': 'crm.lead',
                'view_mode': 'form',
                'res_id': self.lead_id.id,
                'target': 'current',
            }

    # Restricción de seguridad para evitar errores de captura
    @api.constrains('cylinder_qty')
    def _check_cylinder_qty(self):
        for record in self:
            if record.cylinder_qty <= 0:
                raise ValidationError("La cantidad de cilindros a evaluar debe ser al menos 1.")

    @api.constrains('cylinder_qty', 'allocated_qty')
    def _check_quantities(self):
        """Previene que el usuario agrupe más cilindros de los que existen en el total."""
        for survey in self:
            if survey.allocated_qty > survey.cylinder_qty:
                raise ValidationError(
                    f"Inconsistencia: Has asignado {survey.allocated_qty} cilindros en los grupos, "
                    f"pero el total declarado es de solo {survey.cylinder_qty}."
                )

    def action_confirm(self):
        """Pasa de Levantamiento a Orden de Trabajo, valida grupos, empaques y actualiza la referencia"""
        for record in self:
            # 1. VALIDACIÓN DE GRUPOS Y OPERACIONES (Refactorizado para la nueva arquitectura 1:N:N)
            if not record.group_ids:
                raise ValidationError("No puedes confirmar una Orden de Trabajo sin haber definido al menos un Grupo de Cilindros.")
            
            # Validar que al menos un grupo tenga líneas de registro operativo
            has_operations = any(group.operational_record_ids for group in record.group_ids)
            if not has_operations:
                raise ValidationError("Los grupos definidos no tienen tareas operativas (Registro Operativo) asignadas.")

            # 2. VALIDACIÓN DE CANTIDADES (Para evitar errores de captura del usuario)
            if record.allocated_qty != record.cylinder_qty:
                raise ValidationError(
                    f"No puedes confirmar. Has declarado un total de {record.cylinder_qty} cilindros, "
                    f"pero has asignado {record.allocated_qty} en los grupos. Deben coincidir exactamente."
                )

            # 3. GESTIÓN DE PRODUCTOS (Requisición de Empaques)
            # Buscamos de forma insensible a mayúsculas/minúsculas (ilike) por si alguien escribe "Sellos" o "sellos"
            category = self.env['product.category'].search([
                ('name', 'ilike', 'SELLOS')
            ], limit=1)
            
            # Si no existe la categoría SELLOS, usaremos la categoría por defecto 'All' de Odoo para que no falle
            # default_category_id = category.id if category else self.env.ref('product.product_category_all').id
            
            for line in record.cylinder_survey_line_ids:
                # Evitar errores si intentan confirmar una línea vacía
                if not line.code_label:
                    raise ValidationError("Una de las líneas de empaque no tiene el código definido (code_label).")

                # 🔍 Buscar producto por código
                product = self.env['product.product'].search([
                    ('default_code', '=', line.code_label)
                ], limit=1)

                # 🛠️ Crear producto si no existe
                if not product:
                    product = self.env['product.product'].create({
                        'name': line.description_label or f"Empaque {line.code_label}",
                        'default_code': line.code_label,
                        'type': 'consu',  # Consumible es correcto en Odoo 18 para este tipo de piezas
                        'categ_id': category.id,
                    })

                # 🔗 Asignar el producto a la línea
                line.product_id = product.id
            
            # 4. CAMBIO DE NOMENCLATURA Y ESTADO
            new_name = record.name
            # startswith nos asegura que no reemplacemos 'LEV-' si por casualidad aparece a la mitad de un texto
            if new_name and new_name.startswith('LEV-'):
                new_name = new_name.replace('LEV-', 'OT-', 1)
                
            record.write({
                'state': 'confirmed',
                'name': new_name
            })
    
    def action_quoted(self):
        """Pasa de Cotización a Orden de Trabajo"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError("Solo puedes confirmar una Orden de Trabajo que esté en estado 'Cotización'.")
            
            record.write({
                'state': 'quoted'
            })

    def action_set_draft(self):
        """Permite regresar a borrador y restaura el prefijo original"""
        for record in self:
            new_name = record.name
            if new_name and new_name.startswith('OT-'):
                new_name = new_name.replace('OT-', 'LEV-', 1)
                
            record.write({
                'state': 'draft',
                'name': new_name
            })

    def action_cancel(self):
        """Cancela el registro"""
        self.write({'state': 'cancel'})

    def action_create_purchase_order(self):
        for record in self:

            # Obtener proveedor desde el primer producto
            supplier = False

            for line in record.cylinder_survey_line_ids:
                if line.product_id.seller_ids:
                    supplier = line.product_id.seller_ids[0].partner_id
                    break

            if not supplier:
                raise UserError("No hay proveedor definido en los productos.")            
            
            po = self.env['purchase.order'].create({
                'date_planned': record.date_delivery,
                'survey_id': record.id,
                'partner_id': supplier.id
            })

            for line in record.cylinder_survey_line_ids:

                self.env['purchase.order.line'].create({
                    'order_id': po.id,
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_qty': line.unit_total,
                    'price_unit': line.product_id.standard_price,
                    'date_planned': record.date_delivery,
                })
                
            return {
                'type': 'ir.actions.act_window',
                'name': 'Orden de Compra',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': po.id,
            }

    @api.depends('group_ids.operational_record_ids.hr', 'group_ids.operational_record_ids')
    def _compute_operational_totals(self):
        for record in self:
            # Obtener todas las líneas de todos los grupos del levantamiento
            all_lines = record.group_ids.mapped('operational_record_ids')
            record.total_tasks = len(all_lines)
            
            total_h = 0.0
            for group in record.group_ids:
                group_hours = sum(line.hr for line in group.operational_record_ids)
                total_h += (group_hours * group.quantity)
            
            record.total_hours = total_h
        
    @api.depends('group_ids.quantity')
    def _compute_allocated_qty(self):
        for survey in self:
            survey.allocated_qty = sum(survey.group_ids.mapped('quantity'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("impsa.cylinder.survey")
                    or "Nuevo"
                )

        return super(CylinderSurvey, self).create(vals_list)
