<<<<<<< HEAD
from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError, UserError

=======
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
>>>>>>> 1a391fe80b61aba2c9b6270a7d8b0625aac85b09

class PurchaseCylinder(models.Model):
    _inherit = "purchase.order"

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento de Cilindro",
        ondelete="set null",
        index=True,
        copy=False,
        groups="impsa_cylinder_survey.group_cylinder_survey_user"
    )

    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count",
        compute_sudo=True
<<<<<<< HEAD
    )

    approval_request_id = fields.Many2one(
        'approval.request',
        string='Solicitud de Aprobación',
        copy=False
    )

    is_my_approval_turn = fields.Boolean(
        string='Es mi turno de aprobar',
        compute='_compute_is_my_approval_turn'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Valida ANTES de crear: sin productos no se guarda la orden,
        así no se gasta un folio (P000xx) en una orden vacía."""
        if not self.env.context.get('skip_po_line_check'):
            for vals in vals_list:
                if not vals.get('order_line'):
                    raise ValidationError(_(
                        "Faltan algunos campos obligatorios. Debes agregar al menos un producto en las líneas de la orden."
                    ))
        return super().create(vals_list)

=======
    )    
>>>>>>> 1a391fe80b61aba2c9b6270a7d8b0625aac85b09
    @api.depends('survey_id')
    def _compute_cylinder_survey_count(self):
        for record in self:
            record.cylinder_survey_count = 1 if record.sudo().survey_id else 0
<<<<<<< HEAD

    @api.depends('state', 'approval_request_id')
    @api.depends_context('uid')
    def _compute_is_my_approval_turn(self):
        is_admin = self.env['approval.request']._is_approval_admin()
        for order in self:
            request = order.sudo().approval_request_id
            pending = request.approver_ids.filtered(lambda a: a.status == 'pending')
            mine = pending.filtered(lambda a: a.user_id == self.env.user)
            # El aprobador ve los botones en su turno; el Administrador, siempre
            order.is_my_approval_turn = bool(
                order.state == 'to approve' and (mine or (is_admin and pending))
            )

    def action_view_survey(self):
        self.ensure_one()
=======
            
    def action_view_survey(self):
        self.ensure_one()

>>>>>>> 1a391fe80b61aba2c9b6270a7d8b0625aac85b09
        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamiento',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'form',
            'res_id': self.survey_id.id,
        }
<<<<<<< HEAD

    def action_view_approval_request(self):
        """Acción nativa del Smart Button hacia Aprobaciones."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Solicitud de Aprobación'),
            'res_model': 'approval.request',
            'view_mode': 'form',
            'res_id': self.approval_request_id.id,
        }

    # ------------------------------------------------------------------
    # Botones Aprobar / Rechazar en la orden (usan los métodos nativos
    # de Aprobaciones, igual que los botones de la solicitud)
    # ------------------------------------------------------------------
    def _get_my_pending_approver(self):
        self.ensure_one()
        request = self.sudo().approval_request_id
        pending = request.approver_ids.sorted('sequence').filtered(lambda a: a.status == 'pending')
        approver = pending.filtered(lambda a: a.user_id == self.env.user)[:1]
        # El Administrador de Aprobaciones puede decidir el turno de cualquiera
        if not approver and self.env['approval.request']._is_approval_admin():
            approver = pending[:1]
        if not approver:
            raise UserError(_('No tienes una aprobación pendiente en esta orden.'))
        # Sin sudo: la decisión queda a nombre del usuario que presionó
        return (
            self.env['approval.request'].browse(request.id),
            self.env['approval.approver'].browse(approver.id),
        )

    def action_approval_approve(self):
        for order in self:
            request, approver = order._get_my_pending_approver()
            request.action_approve(approver)
        return True

    def action_approval_refuse(self):
        for order in self:
            request, approver = order._get_my_pending_approver()
            request.action_refuse(approver)
        return True

    # ------------------------------------------------------------------
    # Aprobadores: se deciden aquí, NO en la categoría
    # ------------------------------------------------------------------
    def _get_approval_users(self):
        """Usuarios que deben aprobar esta orden, EN ORDEN.

        1) Si el comprador es del Área Operativa (o de un subdepartamento),
           primero siempre aprueba el Gerente de Producción.
           Área Comercial, Aprobadores, otros o sin departamento: se salta ese paso.
        2) Después, según el monto total de la orden:
              <= 999.00           -> Coordinador de Compras
              999.01 a 49,999.00  -> Gerente Operativo
              >  49,999.00        -> Director
        """
        self.ensure_one()
        module = 'impsa_cylinder_survey'

        def get_user(xml_id):
            user = self.env.ref('%s.%s' % (module, xml_id), raise_if_not_found=False)
            if not user:
                raise ValidationError(_(
                    'No se encontró el usuario aprobador "%s". '
                    'Revisa que exista en Ajustes > Usuarios.') % xml_id)
            return user

        approvers = self.env['res.users']

        # Paso 1: departamento del comprador
        buyer = self.user_id or self.create_uid or self.env.user
        department = buyer.sudo().employee_id.department_id
        operativa = self.env.ref('%s.dep_area_operativa' % module, raise_if_not_found=False)
        if department and operativa:
            operativa_ids = self.env['hr.department'].sudo().search(
                [('id', 'child_of', operativa.id)]).ids
            if department.id in operativa_ids:
                approvers |= get_user('user_gerente_produccion')

        # Paso 2: monto total
        amount = self.amount_total
        if amount <= 999.00:
            approvers |= get_user('user_coordinador_compras')
        elif amount <= 49999.00:
            approvers |= get_user('user_gerente_operativo')
        else:
            approvers |= get_user('user_director')

        return approvers

    # ------------------------------------------------------------------
    # Confirmación: crea la solicitud en Aprobaciones IMPSA
    # ------------------------------------------------------------------
    def button_confirm(self):
        """Valida productos y crea la solicitud en Aprobaciones IMPSA."""
        to_confirm = self.browse()
        for order in self:
            if not order.order_line:
                raise ValidationError(_(
                    "Faltan algunos campos obligatorios. Debes agregar al menos un producto en las líneas de la orden."
                ))

            if order.state not in ('draft', 'sent'):
                to_confirm |= order
                continue

            category = self.env.ref('impsa_cylinder_survey.approval_cat_po_impsa', raise_if_not_found=False)
            if not category:
                category = self.env['approval.category'].search([('name', '=', 'Aprobaciones IMPSA')], limit=1)

            if not category:
                # Sin categoría de aprobación: flujo normal de Compras
                to_confirm |= order
                continue

            approvers = order._get_approval_users()
            if not approvers:
                raise ValidationError(_('No hay aprobadores definidos para esta orden.'))

            request = order.sudo().approval_request_id
            # Se crea una solicitud nueva si no existe o si la anterior terminó rechazada/cancelada/en borrador
            if not request or request.request_status in ('refused', 'cancel', 'new'):
                product_lines = []
                for line in order.order_line.filtered(lambda l: l.product_id):
                    product_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'description': line.name or line.product_id.display_name,
                        'quantity': line.product_qty,
                        'product_uom_id': line.product_uom_id.id,
                    }))

                request_vals = {
                    'name': _('Aprobación para Orden: %s') % order.name,
                    'category_id': category.id,
                    'request_owner_id': self.env.user.id,
                    'amount': order.amount_total,
                    'partner_id': order.partner_id.id,
                    'reference': order.name,
                    'purchase_order_id': order.id,
                    'product_line_ids': product_lines,
                    # Los aprobadores salen del código, no de la categoría
                    'approver_ids': [
                        Command.create({
                            'user_id': user.id,
                            'status': 'new',
                            'required': True,
                            'sequence': index,
                        })
                        for index, user in enumerate(approvers, start=1)
                    ],
                }
                approval_request = self.env['approval.request'].sudo().create(request_vals)
                approval_request.action_confirm()
                order.approval_request_id = approval_request.id

                # Aviso en el chatter: a quién le cae la aprobación
                first = approval_request.approver_ids.sorted('sequence').filtered(
                    lambda a: a.status == 'pending')[:1]
                if first:
                    chain = approval_request.approver_ids.sorted('sequence') - first
                    body = _('📤 ENVIADA A APROBACIÓN - Asignada a: %s.') % first.user_id.name
                    if chain:
                        body += _(' Después: %s.') % ', '.join(chain.mapped('user_id.name'))
                    order.sudo().message_post(
                        body=body,
                        author_id=first.user_id.partner_id.id,
                        subtype_xmlid='mail.mt_note',
                    )

            # mail_notrack: no deja el registro automático "Solicitud de cotización → Por aprobar"
            order.with_context(mail_notrack=True).write({'state': 'to approve'})

        if to_confirm:
            return super(PurchaseCylinder, to_confirm).button_confirm()
        return True

    def button_approve(self, force=False):
        """La aprobación de la orden solo se hace desde Aprobaciones
        (o con los botones de la orden), respetando la secuencia."""
        if not self.env.context.get('approval_sync'):
            for order in self:
                request = order.sudo().approval_request_id
                if request and request.request_status in ('new', 'pending'):
                    raise UserError(_(
                        'La orden %s está en proceso de aprobación. '
                        'Debe aprobarse con los botones Aprobar / Rechazar.') % order.name)
        return super(PurchaseCylinder, self).button_approve(force=force)

    def _approval_allowed(self):
        # Cuando la confirmación viene de Aprobaciones, siempre se permite
        if self.env.context.get('approval_sync'):
            return True
        return super()._approval_allowed()

    def action_rfq_send(self):
        """Envío nativo bloqueado si no hay productos."""
        for order in self:
            if not order.order_line:
                raise ValidationError(_(
                    "Faltan algunos campos obligatorios. No puedes enviar una solicitud de cotización sin productos."
                ))
        return super(PurchaseCylinder, self).action_rfq_send()
=======
        
    def button_confirm(self):
        for order in self:
            products_without_code = order.order_line.filtered(
                lambda l: not l.product_id.default_code
            )

            if products_without_code:
                product_names = ", ".join(
                    products_without_code.mapped('product_id.display_name')
                )

                raise ValidationError(_(
                    "No puedes confirmar la Orden de Compra porque los siguientes productos no tienen código interno (default_code):\n%s"
                ) % product_names)

        return super().button_confirm()
        
    
>>>>>>> 1a391fe80b61aba2c9b6270a7d8b0625aac85b09
