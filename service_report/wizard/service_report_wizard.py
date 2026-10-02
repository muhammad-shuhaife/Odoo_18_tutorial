from collections import OrderedDict
from datetime import datetime, time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ServiceReportWizard(models.TransientModel):
    _name = 'service.report.wizard'
    _description = 'Service Report Wizard'

    report_type = fields.Selection(
        [('sale', 'Sales'), ('purchase', 'Purchase')],
        required=True,
        default=lambda self: self.env.context.get('default_report_type', 'sale'),
    )
    date_from = fields.Date(string="Date From", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="Date To", required=True, default=fields.Date.context_today)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True
    )

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise UserError(_("'Date From' cannot be after 'Date To'."))

    def _get_report_data(self):
        """Return a list of month groups with lines and totals."""
        self.ensure_one()
        dt_from = datetime.combine(self.date_from, time.min)
        dt_to = datetime.combine(self.date_to, time.max)

        if self.report_type == 'sale':
            line_model, states = 'sale.order.line', ['sale']
            qty_field = 'product_uom_qty'
        else:
            line_model, states = 'purchase.order.line', ['purchase', 'done']
            qty_field = 'product_qty'

        domain = [
            ('order_id.state', 'in', states),
            ('order_id.company_id', '=', self.company_id.id),
            ('order_id.date_order', '>=', dt_from),
            ('order_id.date_order', '<=', dt_to),
            ('display_type', '=', False),
            ('product_id.type', '=', 'service'),
        ]

        lines = self.env[line_model].search(domain)
        lines = lines.sorted(key=lambda l: (l.order_id.date_order, l.id))

        groups = OrderedDict()
        for line in lines:
            d = fields.Datetime.context_timestamp(self, line.order_id.date_order)
            key = d.strftime('%Y-%m')
            grp = groups.setdefault(key, {
                'name': d.strftime('%B %Y'),
                'lines': [],
                'qty': 0.0,
                'amount': 0.0
            })
            qty = line[qty_field]
            amount = line.price_subtotal
            grp['lines'].append({
                'date': d.strftime('%d-%b-%Y'),
                'service': line.product_id.display_name,
                'qty': qty,
                'amount': amount,
            })
            grp['qty'] += qty
            grp['amount'] += amount

        return list(groups.values())

    def action_print(self):
        self.ensure_one()
        return self.env.ref('service_report.action_report_service').report_action(self)