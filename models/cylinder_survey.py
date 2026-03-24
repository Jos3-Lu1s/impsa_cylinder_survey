from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class CylinderSurvey(models.Model):
    _name = "impsa.cylinder.survey"
    _description = "Levantamiento de Cilindros (F-05-01)"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Referencia", required=True, copy=False, readonly=True, default="Nuevo"
    )

    partner_id = fields.Many2one(
        "res.partner", string="Cliente", required=True, tracking=True, ondelete='restrict'
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
        "impsa.operational.record.line",
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

    date = fields.Date(string="Fecha", default=fields.Date.context_today, index=True)
    description = fields.Text(string="Descripción")

    rotula_id = fields.Many2one(
        "product.product",
        string="Rotula",
        domain="[('categ_id.name', '=', 'FERRETERIA')]",
        ondelete='restrict'
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
        ondelete='restrict',
        required=True
    )

    cylinder_to_code = fields.Char(
        string="Código del Cilindro",
        related="cylinder_to.code",
        store=False
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
    ], string='Estado', default='draft', tracking=True, copy=False, index=True)

    cylinder_type = fields.Selection([
        ('hydraulic', 'Hidráulico'),
        ('pneumatic', 'Neumático')
    ],string='Tipo de Cilindro')

    is_standardized = fields.Boolean(
        string='Normalizado'
    )
    
    purchase_order_ids = fields.One2many(
        "purchase.order",
        "survey_id",
        string="Órdenes de Compra"
    )

    purchase_order_count = fields.Integer(
        compute="_compute_purchase_order_count"
    )

    lead_id = fields.Many2one(
        'crm.lead',
        string="Oportunidad",
        ondelete='set null'
    )
    
    sale_order_id = fields.One2many(
        'sale.order',
        'survey_id',
        string="Orden de Venta",
        ondelete='set null'
    )

    lead_count = fields.Integer(
        string="Oportunidades",
        compute="_compute_lead_count"
    )
    
    sale_count = fields.Integer(
        string="Órdenes de Venta",
        compute="_compute_sale_count"
    )


    ''' ------------------------
        COMPUTE METHODS
    -------------------------'''

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)

    @api.depends('lead_id')
    def _compute_lead_count(self):
        for rec in self:
            rec.lead_count = 1 if rec.lead_id else 0
            
    @api.depends('sale_order_id')
    def _compute_sale_count(self):
        for rec in self:
            rec.sale_count = len(rec.group_ids) if rec.sale_order_id else 0

    @api.depends('group_ids.operational_record_ids.hr', 'group_ids.operational_record_ids', 'group_ids.quantity')
    def _compute_operational_totals(self):
        for record in self:
            total_tasks = 0
            total_h = 0.0
            for group in record.group_ids:
                lines = group.operational_record_ids
                total_tasks += len(lines)
                group_hours = sum(lines.mapped('hr'))
                total_h += (group_hours * group.quantity)
            
            record.total_tasks = total_tasks
            record.total_hours = total_h
        
    @api.depends('group_ids.quantity')
    def _compute_allocated_qty(self):
        for survey in self:
            survey.allocated_qty = sum(survey.group_ids.mapped('quantity'))

    ''' ------------------------
        CONSTRAINS
    -------------------------'''

    # Restricción de seguridad para evitar errores de captura
    @api.constrains('cylinder_qty')
    def _check_cylinder_qty(self):
        for record in self:
            if record.cylinder_qty <= 0:
                raise ValidationError(_("La cantidad de cilindros a evaluar debe ser al menos 1."))

    @api.constrains('cylinder_qty', 'allocated_qty')
    def _check_quantities(self):
        """Previene que el usuario agrupe más cilindros de los que existen en el total."""
        for survey in self:
            if survey.allocated_qty > survey.cylinder_qty:
                raise ValidationError(
                    f"Inconsistencia: Has asignado {survey.allocated_qty} cilindros en los grupos, "
                    f"pero el total declarado es de solo {survey.cylinder_qty}."
                )

    @api.constrains(
        'cylinder_to', 'barrel_inner_diameter', 'barrel_outer_diameter', 'barrel_length',
        'diameter_rod', 'rod_length', 'piston_diameter', 'piston_length', 
        'head_diameter', 'head_length', 'stroke_length'
    )
    def _check_required_dimensions_by_type(self):
        for rec in self:
            if not rec.cylinder_to or not rec.cylinder_to.code:
                continue
                
            code = rec.cylinder_to.code
            missing_components = []

            # Evaluamos por bloque de pieza en lugar de campo por campo
            if code == 'CE-OT':
                if rec.barrel_inner_diameter <= 0.0:
                    missing_components.append('Diámetro Interior de la Camisa')

            elif code in ['CE-DE', 'CE-SE']:
                if rec.barrel_inner_diameter <= 0.0 or rec.barrel_outer_diameter <= 0.0 or rec.barrel_length <= 0.0:
                    missing_components.append('Camisa')
                if rec.diameter_rod <= 0.0 or rec.rod_length <= 0.0:
                    missing_components.append('Vástago')
                if rec.piston_diameter <= 0.0 or rec.piston_length <= 0.0:
                    missing_components.append('Émbolo')
                if rec.head_diameter <= 0.0 or rec.head_length <= 0.0:
                    missing_components.append('Cabeza')
                if rec.stroke_length <= 0.0:
                    missing_components.append('Carrera')

            if missing_components:
                componentes = ", ".join(missing_components)
                raise ValidationError(
                    f"Faltan medidas para el cilindro '{rec.cylinder_to.name}'.\n\n"
                    f"Asegúrate de registrar valores mayores a 0 en: {componentes}."
                )

    ''' ------------------------
        ACTIONS
    -------------------------'''

    def action_view_purchase_orders(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de Compra',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('survey_id', '=', self.id)],
        }

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
            
    def action_view_sale_order(self):
        self.ensure_one()
        
        if self.sale_order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Orden de Venta',
                'res_model': 'sale.order',
                'view_mode': 'list,form',
                'domain': [('survey_id', '=', self.id)],
            }

    def action_confirm(self):
        """Valida e inicializa productos para pasar a Orden de Trabajo."""
        for record in self:
            # 1. Validaciones
            if not record.group_ids:
                raise ValidationError("Define al menos un Grupo de Cilindros.")
            if not any(group.operational_record_ids for group in record.group_ids):
                raise ValidationError("Los grupos no tienen tareas operativas asignadas.")
            if record.allocated_qty != record.cylinder_qty:
                raise ValidationError(
                    f"Debes asignar exactamente {record.cylinder_qty} cilindros. "
                    f"Actualmente hay {record.allocated_qty}."
                )
            
            # 2. Creación de Productos en Lote
            Product = self.env['product.product']
            category = self.env['product.category'].search([('name', '=', 'SELLOS')], limit=1)
            categ_id = category.id if category else False

            # Extraer códigos de los empaques de este registro
            lines = record.cylinder_survey_line_ids
            if any(not line.code_label for line in lines):
                raise ValidationError("Una o más líneas de empaque no tienen código definido (code_label).")

            # en vez de buscar producto por producto se hace una busqueda masiva
            codes = lines.mapped('code_label')
            existing_products = Product.search([('default_code', 'in', codes)])
            product_map = {p.default_code: p for p in existing_products}
            seen_codes = set(product_map.keys())

            # Preparar productos a crear
            products_to_create_vals = []
            for line in lines:
                code = line.code_label
                if code not in seen_codes:
                    seen_codes.add(code)
                    products_to_create_vals.append({
                        'name': line.description_label or f"Empaque {code}",
                        'default_code': code,
                        'type': 'consu', 
                        'categ_id': categ_id,
                    })

            # Crear en lote
            if products_to_create_vals:
                new_products = Product.create(products_to_create_vals)
                for p in new_products:
                    product_map[p.default_code] = p

            # Asignar productos a las líneas
            for line in lines:
                line.product_id = product_map[line.code_label]
            
            if record.group_ids:
                count_quotation=0
                for group in record.group_ids:
                    if group.sale_order_id and group.sale_order_id.state == 'sale':
                        count_quotation+=1
                if count_quotation == 0:
                    raise ValidationError("Debe existir al menos 1 cotización (orden de venta) aceptada por el cliente.")

            # 3. Cambio de Estado                
            record.write({'state': 'confirmed'})
    
    def action_quoted(self):
        """Pasa de Cotización a Orden de Trabajo"""
        for record in self:
            if not record.group_ids:
                raise ValidationError(_("Debes agregar al menos un 'Identificador del Grupo'"))
            for group in record.group_ids:

                # Evitar duplicados
                if group.sale_order_id:
                    continue

                sale_order = self.env['sale.order'].create({
                    'survey_id': self.id,
                    'partner_id': record.partner_id.id,
                    'requeriments_work_order': record.name,
                    'group_requeriments_work_order': group.name,
                })

                    # Guardar referencia en el grupo
                group.sale_order_id = sale_order.id
        record.write({
               'state': 'quoted'
           })         

    def action_set_draft(self):
        """Permite regresar a borrador"""
        for record in self: 
            record.write({'state': 'draft'})

    def action_cancel(self):
        """Cancela el registro"""
        for record in self:
            if record.state == 'confirmed':
                raise ValidationError(_("No puedes cancelar un registro que ya es una Orden de Trabajo confirmada. Reviértelo primero."))
            record.write({'state': 'cancel'})

    def action_create_purchase_order(self):
        """Crea Órdenes de Compra agrupadas por proveedor del empaque."""
        self.ensure_one()

        if not self.cylinder_survey_line_ids:
             raise UserError(_("No hay empaques para generar órdenes de compra."))

        # Agrupar líneas por proveedor
        lines_by_supplier = {}
        planned_datetime = fields.Datetime.to_datetime(self.date_delivery) if self.date_delivery else fields.Datetime.now()

        for line in self.cylinder_survey_line_ids:
            seller = line.product_id.seller_ids[:1]
            if not seller:
                raise UserError(_(
                    "El producto '%(prod)s' no tiene un proveedor definido (pestaña Compras).",
                    prod=line.product_id.display_name
                ))

            supplier = seller.partner_id
            if supplier not in lines_by_supplier:
                lines_by_supplier[supplier] = []

            lines_by_supplier[supplier].append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_qty': line.unit_total,
                'price_unit': seller.price, #Usar precio del vendor, NO el standard_price (costo).
                'date_planned': planned_datetime,
            }))

        # Crear las POs iterando por cada proveedor detectado.
        created_pos = self.env['purchase.order']
        for supplier, po_lines in lines_by_supplier.items():
            po = self.env['purchase.order'].create({
                'survey_id': self.id,
                'partner_id': supplier.id,
                'order_line': po_lines,
                'date_planned': planned_datetime,
            })
            created_pos += po

        # Retornar vista dinámica dependiendo si se creó 1 o varias POs
        if len(created_pos) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Orden de Compra'),
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': created_pos.id,
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Órdenes de Compra'),
                'res_model': 'purchase.order',
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_pos.ids)],
            }


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("impsa.cylinder.survey")
                    or "Nuevo"
                )

        return super(CylinderSurvey, self).create(vals_list)
