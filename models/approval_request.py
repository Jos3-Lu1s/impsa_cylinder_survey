from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    purchase_order_id = fields.Many2one(
        "purchase.order",
        string="Orden de Compra",
        ondelete="cascade",
        copy=False
    )

    purchase_order_count = fields.Integer(
        string="Compras",
        compute="_compute_purchase_order_count"
    )

    # Botones NATIVOS de la solicitud: se muestran también al administrador
    show_approve_refuse = fields.Boolean(compute='_compute_show_buttons')
    show_withdraw = fields.Boolean(compute='_compute_show_buttons')
    show_cancel = fields.Boolean(compute='_compute_show_buttons')

    @api.depends('request_status', 'approver_ids.status', 'approver_ids.user_id', 'request_owner_id')
    @api.depends_context('uid')
    def _compute_show_buttons(self):
        user = self.env.user
        is_admin = self._is_approval_admin()
        for request in self:
            lines = request.sudo().approver_ids
            own = lines.filtered(lambda a: a.user_id == user)
            pending = lines.filtered(lambda a: a.status == 'pending')
            decided = lines.filtered(lambda a: a.status in ('approved', 'refused'))
            status = request.request_status
            request.show_approve_refuse = status == 'pending' and bool(
                own.filtered(lambda a: a.status == 'pending') or (is_admin and pending))
            request.show_withdraw = status in ('pending', 'approved', 'refused') and bool(
                own.filtered(lambda a: a.status in ('approved', 'refused')) or (is_admin and decided))
            request.show_cancel = status in ('pending', 'approved', 'refused') and bool(
                is_admin or request.request_owner_id == user or own)

    def _default_admin_approver(self, kind):
        """Si el administrador no es el aprobador, los botones nativos actúan sobre
        la línea que corresponde: la que está en turno (aprobar/rechazar) o la última
        decisión (anular). Devuelve None cuando no aplica."""
        if len(self) != 1 or not self._is_approval_admin():
            return None
        lines = self.sudo().approver_ids.sorted('sequence')
        mine = lines.filtered(lambda a: a.user_id == self.env.user)
        if kind == 'withdraw':
            if mine.filtered(lambda a: a.status in ('approved', 'refused')):
                return None
            line = lines.filtered(lambda a: a.status == 'refused')[:1] \
                or lines.filtered(lambda a: a.status == 'approved')[-1:]
        else:
            if mine.filtered(lambda a: a.status == 'pending'):
                return None
            line = lines.filtered(lambda a: a.status == 'pending')[:1]
        return self.env['approval.approver'].browse(line.id) if line else None

    @api.depends('purchase_order_id')
    def _compute_purchase_order_count(self):
        for request in self:
            request.purchase_order_count = 1 if request.purchase_order_id else 0

    # ------------------------------------------------------------------
    # Control del administrador
    # ------------------------------------------------------------------
    def _is_approval_admin(self):
        """Administrador: tiene "Aprobaciones: Administrador" o "Función: Administrador".
        Puede aprobar, rechazar y anular por cualquiera. Nada más."""
        user = self.env.user
        return user.has_group('approvals.group_approval_manager') \
            or user.has_group('base.group_system')

    def _check_not_acting_for_other(self, approver):
        """CANDADO: nadie puede aprobar o rechazar el turno de otra persona,
        salvo el Administrador de Aprobaciones."""
        if approver and isinstance(approver, models.BaseModel) \
                and not self.env.su and not self._is_approval_admin():
            for line in approver:
                if line.user_id != self.env.user:
                    raise UserError(_(
                        'No puedes aprobar ni rechazar en nombre de %s. '
                        'Esta aprobación le corresponde a él.') % line.user_id.name)

    def _close_activities_of(self, user):
        """Cierra la actividad pendiente del usuario en cuyo nombre se decidió."""
        for request in self:
            if user and user != self.env.user:
                request.sudo().activity_ids.filtered(
                    lambda a: a.user_id == user).sudo().action_feedback()

    # ------------------------------------------------------------------
    # Mensajes en el chatter de la orden de compra
    # ------------------------------------------------------------------
    def _get_acting_line(self, approver=None):
        """Línea que se aprueba o rechaza (se calcula ANTES de ejecutar)."""
        self.ensure_one()
        if approver and isinstance(approver, models.BaseModel):
            lines = approver.sudo().filtered(lambda a: a.request_id.id == self.id)
        else:
            lines = self.sudo().approver_ids.filtered(
                lambda a: a.user_id == self.env.user and a.status == 'pending')
        return lines[:1]

    def _get_acting_user(self, approver=None):
        """Dueño de la línea que se aprueba o rechaza."""
        return self._get_acting_line(approver).user_id

    # ------------------------------------------------------------------
    # Roles con varios usuarios: con que UNO del paso apruebe, basta
    # ------------------------------------------------------------------
    def _sync_step_members(self):
        """Todos los usuarios del paso en turno quedan "Por aprobar" y con su actividad."""
        for request in self:
            open_lines = request.sudo().approver_ids.filtered(
                lambda a: a.status in ('new', 'waiting', 'pending'))
            if not open_lines:
                continue
            step = min(open_lines.mapped('sequence'))
            to_activate = open_lines.filtered(
                lambda a: a.sequence == step and a.status in ('new', 'waiting'))
            if not to_activate:
                continue
            to_activate.write({'status': 'pending'})
            for line in to_activate:
                if hasattr(line, '_create_activity'):
                    line._create_activity()
                else:
                    request.sudo().activity_schedule(
                        'approvals.mail_activity_data_approval', user_id=line.user_id.id)

    def _release_step_siblings(self, line):
        """Si uno del paso ya aprobó, los demás del mismo paso quedan fuera."""
        self.ensure_one()
        if not line or line.sudo().status != 'approved':
            return
        siblings = self.sudo().approver_ids.filtered(
            lambda a: a.id != line.id and a.sequence == line.sequence
            and a.status in ('new', 'waiting', 'pending'))
        if siblings:
            self.sudo().activity_ids.filtered(lambda a: a.user_id in siblings.user_id).unlink()
            siblings.unlink()

    def _acting_label(self, line_user):
        """Texto de quién decidió: si fue el admin por otro, lo indica."""
        if line_user and line_user != self.env.user:
            return _('%s en nombre de %s') % (self.env.user.name, line_user.name)
        return (line_user or self.env.user).name

    def _post_order_message(self, order, body):
        """Nota interna en la orden, con la foto de quien actuó."""
        order.sudo().message_post(
            body=body,
            author_id=self.env.user.partner_id.id,
            subtype_xmlid='mail.mt_note',
        )

    # ------------------------------------------------------------------
    # Aprobar / Rechazar / Cancelar
    # ------------------------------------------------------------------
    def action_approve(self, approver=None):
        """Aprueba, avisa en la orden y, si ya terminó, la confirma."""
        if approver is None:
            approver = self._default_admin_approver('approve')
        self._check_not_acting_for_other(approver)
        lines = {request.id: request._get_acting_line(approver) for request in self}
        res = super(ApprovalRequest, self).action_approve(approver=approver)
        for request in self:
            req = request.sudo()
            order = req.purchase_order_id
            line = lines.get(request.id)
            actor = line.user_id if line else self.env['res.users']
            request._close_activities_of(actor)

            # Rol con varios usuarios: uno aprobó, los demás del paso salen; sigue el siguiente paso
            request._release_step_siblings(line)
            request._sync_step_members()
            if not order:
                continue

            if actor:
                open_lines = req.approver_ids.filtered(
                    lambda a: a.status in ('new', 'waiting', 'pending'))
                who = request._acting_label(actor)
                if open_lines:
                    step = min(open_lines.mapped('sequence'))
                    names = _(' o ').join(open_lines.filtered(
                        lambda a: a.sequence == step).mapped('user_id.name'))
                    body = _('✔️ APROBADO por %s - Pendiente que apruebe: %s.') % (who, names)
                else:
                    body = _('✔️ APROBADO por %s - Todas las aprobaciones completas.') % who
                request._post_order_message(order, body)

            if req.request_status == 'approved' and order.state == 'to approve':
                order.with_context(approval_sync=True, mail_notrack=True).button_approve()
        return res

    def action_refuse(self, approver=None):
        """Rechaza, avisa en la orden y la cancela."""
        if approver is None:
            approver = self._default_admin_approver('refuse')
        self._check_not_acting_for_other(approver)
        actors = {request.id: request._get_acting_user(approver) for request in self}
        res = super(ApprovalRequest, self).action_refuse(approver=approver)
        for request in self:
            req = request.sudo()
            order = req.purchase_order_id
            actor = actors.get(request.id)
            request._close_activities_of(actor)
            if not order:
                continue

            if actor:
                request._post_order_message(
                    order,
                    _('❌ RECHAZADO por %s - Se termina el flujo de aprobación.')
                    % request._acting_label(actor))

            if req.request_status == 'refused' and order.state in ('draft', 'sent', 'to approve'):
                order.with_context(approval_sync=True, mail_notrack=True).button_cancel()
        return res

    def _get_withdrawing_user(self, approver=None):
        """Dueño de la decisión que se anula (se calcula ANTES de ejecutar)."""
        self.ensure_one()
        if approver and isinstance(approver, models.BaseModel):
            lines = approver.sudo().filtered(lambda a: a.request_id.id == self.id)
        else:
            lines = self.sudo().approver_ids.filtered(
                lambda a: a.user_id == self.env.user and a.status in ('approved', 'refused'))
        return lines[:1].user_id

    def action_withdraw(self, approver=None):
        """Anular: retira la decisión, avisa en la orden y la regresa a "Por aprobar"."""
        if approver is None:
            approver = self._default_admin_approver('withdraw')
        self._check_not_acting_for_other(approver)
        owners = {request.id: request._get_withdrawing_user(approver) for request in self}
        res = super(ApprovalRequest, self).action_withdraw(approver=approver)
        for request in self:
            req = request.sudo()
            order = req.purchase_order_id
            owner = owners.get(request.id)
            if not order or not owner or req.request_status not in ('pending', 'new'):
                continue

            # La orden vuelve a "Por aprobar" (si estaba confirmada o cancelada)
            if order.state in ('purchase', 'cancel'):
                ctx_order = order.with_context(approval_sync=True, mail_notrack=True)
                if ctx_order.state == 'purchase':
                    ctx_order.button_cancel()  # Odoo avisa si ya tiene recepciones o facturas
                ctx_order.button_draft()
                ctx_order.write({'state': 'to approve'})

            current = req.approver_ids.sorted('sequence').filtered(
                lambda a: a.status == 'pending')[:1]
            body = _('↩️ APROBACIÓN ANULADA por %s') % request._acting_label(owner)
            if current:
                body += _(' - Pendiente que apruebe: %s.') % current.user_id.name
            request._post_order_message(order, body)
        return res

    def action_cancel(self):
        """Cancela la solicitud, avisa en la orden y la cancela."""
        res = super(ApprovalRequest, self).action_cancel()
        for request in self:
            req = request.sudo()
            order = req.purchase_order_id
            if order and req.request_status == 'cancel' \
                    and order.state in ('draft', 'sent', 'to approve'):
                request._post_order_message(
                    order,
                    _('⚠️ SOLICITUD CANCELADA por %s.') % self.env.user.name)
                order.with_context(approval_sync=True, mail_notrack=True).button_cancel()
        return res

    def action_view_purchase_order(self):
        """Acción nativa para abrir la Orden de Compra asociada."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Orden de Compra'),
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_id.id,
            'target': 'current',
        }

    def action_open_purchase_orders(self):
        """El botón nativo "Órdenes de compra" también abre la orden vinculada
        (con sus botones Aprobar / Rechazar), no una lista vacía."""
        self.ensure_one()
        return self.action_view_purchase_order()