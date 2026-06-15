from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError
import base64

class SaleOrderSmart(models.Model):
    _inherit = 'sale.order'

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento de Origen",
        ondelete="set null",
        copy=False,
        help="Levantamiento técnico del cual se generó esta cotización.",
        groups="impsa_cylinder_survey.group_cylinder_survey_user"
    )

    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count",
        compute_sudo=True
    )

    requeriments_work_order=fields.Text(string="Levantamiento/OT", store=True, readonly=True)
    group_requeriments_work_order=fields.Text(string="Grupo Relacionado", store=True, readonly=True)

    delivery_days = fields.Integer(
        string="Días de entrega",
        compute="_compute_delivery_days"
    )
    apu_id = fields.Many2one(
        'impsa.apu.survey',
        string="APU Relacionado",
        ondelete="set null",
        copy=False,
        groups="impsa_cylinder_survey.group_apu_user"
    )

    apu_survey_count = fields.Integer(
        string="APU",
        compute="_compute_apu_survey_count",
        compute_sudo=True
    )

    partner_contact_ids = fields.Many2many(
        'res.partner',
        string='Contactos de la Empresa',
        compute='_compute_partner_contact_ids',
        store=False,
    )

    partner_contact_id = fields.Many2one(
    'res.partner',
    string='Contacto',
    domain="[('id', 'in', partner_contact_ids)]",
    context={'no_company_prefix': True},
    )
    
    dropship_option = fields.Selection(
        [('labnues', 'LAB NUESTRAS INSTALACIONES'), 
         ('labsus', 'LAB SUS INSTALACIONES')],
        string="Entrega",
        default='labnues',
    )
        
    
    def _message_get_suggested_recipients(self, **kwargs):
        # En esta versión devuelve lista, no dict
        # Simplemente retornamos lista vacía
        return []

    @api.onchange('pricelist_id')
    def _onchange_pricelist_product_domain(self):
        """Dispara el recálculo del dominio en todas las líneas."""
        for line in self.order_line:
            line._compute_product_template_domain()

    @api.depends('survey_id')
    def _compute_cylinder_survey_count(self):
        for record in self:
            record.cylinder_survey_count = 1 if record.sudo().survey_id else 0

    @api.depends('apu_id')
    def _compute_apu_survey_count(self):
        for record in self:
            record.apu_survey_count = 1 if record.sudo().apu_id else 0

    def action_view_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamiento',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'form',
            'res_id': self.survey_id.id,
        }
        
    def action_print_proforma_custom(self):
        return self.env.ref('impsa_cylinder_survey.action_report_proforma_custom').report_action(self)
    
    @api.depends('commitment_date')
    def _compute_delivery_days(self):
        for record in self:
            if record.commitment_date:
                today = date.today()
                commit_date = record.commitment_date.date() if record.commitment_date else None

                if commit_date:
                    record.delivery_days = (commit_date - today).days
                else:
                    record.delivery_days = 0
            else:
                record.delivery_days = 0

    def action_view_apu_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'APU',
            'res_model': 'impsa.apu.survey',
            'view_mode': 'form',
            'res_id': self.apu_id.id,
        }

    @api.onchange('partner_id')
    def _onchange_select_pricelist(self):
            pricelist = self.env['product.pricelist'].search([
                        ('contacto_id', '=', self.partner_id.id)  # ← nombre de tu campo Many2one
                    ], limit=1)
            if self.partner_id:
                self.pricelist_id=pricelist.id
                #raise ValidationError(f"La lista de precios es {pricelist}")
                
    def _get_report_base_filename(self):
        self.ensure_one()
        return self.name
    
    def action_view_crm_lead(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Oportunidad',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.opportunity_id.id,
        }

    def action_quotation_send(self):
        self.ensure_one()
    
        # ── Generar PDF pasando el xml_id como string ─────────────────
        report = self.env['ir.actions.report']
        pdf_content, _ = report.sudo()._render_qweb_pdf(
            'impsa_cylinder_survey.action_report_proforma_custom',
            res_ids=[self.id]
        )
    
        # ── Crear adjunto ─────────────────────────────────────────────
        attachment = self.env['ir.attachment'].sudo().create({
            'name': f'{self.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'sale.order',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
    
        # ── Llamar al wizard nativo con el adjunto reemplazado ────────
        result = super().action_quotation_send()
    
        if isinstance(result, dict) and result.get('context'):
            result['context']['default_attachment_ids'] = [attachment.id]
    
        return result

    @api.depends('partner_id')
    def _compute_partner_contact_ids(self):
        for order in self:
            if order.partner_id:
                # Si el cliente es una empresa → traer sus contactos
                if order.partner_id.is_company:
                    order.partner_contact_ids = order.partner_id.child_ids
                # Si el cliente es un contacto → traer hermanos (misma empresa)
                elif order.partner_id.parent_id:
                    order.partner_contact_ids = order.partner_id.parent_id.child_ids
                else:
                    order.partner_contact_ids = False
            else:
                order.partner_contact_ids = False

    @api.onchange('partner_id')
    def _onchange_partner_contact(self):
        """Limpiar el contacto seleccionado si cambia el cliente."""
        self.partner_contact_id = False
        
    def write(self, vals):
        result = super().write(vals)

        if 'state' not in vals:
            return result

        mapeo_crm = {
            'sale':   'won',
            'draft':  'negotiation',
            'sent':   'negotiation',
            'cancel': 'negotiation',
        }

        sync_type = mapeo_crm.get(vals['state'])
        if not sync_type:
            return result

        for order in self:
            lead = order.opportunity_id

            if not lead and order.apu_id:
                lead = order.apu_id.lead_id or (
                    order.apu_id.survey_id and order.apu_id.survey_id.lead_id
                )

            # ✅ lead._sync_stage_from_type, NO self.env['crm.lead']
            if lead and lead._name == 'crm.lead':
                crm_lead = self.env['crm.lead'].browse(lead.id)
                crm_lead._sync_stage_from_type(sync_type)

        return result

    # ✅ action_confirm ya no necesita lógica extra
    def action_confirm(self):
        return super().action_confirm()
