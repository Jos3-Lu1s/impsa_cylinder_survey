from odoo import models, api

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _get_recipients(self):
        recipients = super()._get_recipients()

        if self.env.context.get('default_model') == 'crm.lead':
            return []

        return recipients

    @api.onchange('partner_ids')
    def _onchange_partner_ids_clear(self):
        if self.env.context.get('default_model') == 'crm.lead':
            self.partner_ids = [(5, 0, 0)]

    def get_mail_values(self, res_ids):
        mail_values = super().get_mail_values(res_ids)

        if self.env.context.get('default_model') == 'crm.lead':
            for res_id in res_ids:
                if res_id in mail_values:
                    mail_values[res_id]['partner_ids'] = [(5, 0, 0)]

        return mail_values