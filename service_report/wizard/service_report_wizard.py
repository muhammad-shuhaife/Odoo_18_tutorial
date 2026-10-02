from collections import OrderedDict
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

    def _get_order_payment_date(self, order):
        """Retrieve the latest payment date from posted, paid/in-payment invoices linked to the order."""
        invoices = order.invoice_ids.filtered(
            lambda inv: inv.state == 'posted' and inv.payment_state in ('in_payment', 'paid', 'partial')
        )
        if not invoices:
            return None

        payment_dates = []
        for inv in invoices:
            payments = inv._get_reconciled_payments()
            payment_dates.extend(payments.mapped('date'))

        return max(payment_dates) if payment_dates else None

    def _get_report_data(self):
        """Return a list of month groups with lines and totals grouped by Payment Date."""
        self.ensure_one()

        if self.report_type == 'sale':
            line_model, states = 'sale.order.line', ['sale']
            qty_field = 'product_uom_qty'
        else:
            line_model, states = 'purchase.order.line', ['purchase', 'done']
            qty_field = 'product_qty'

        # Query confirmed service lines that have posted, paid/in-payment invoices
        domain = [
            ('order_id.state', 'in', states),
            ('order_id.company_id', '=', self.company_id.id),
            ('display_type', '=', False),
            ('product_id.type', '=', 'service'),
            ('order_id.invoice_ids.state', '=', 'posted'),
            ('order_id.invoice_ids.payment_state', 'in', ('in_payment', 'paid', 'partial')),
        ]

        lines = self.env[line_model].search(domain)

        # Filter lines where the actual payment date falls within the wizard's date range
        eligible_records = []
        for line in lines:
            payment_date = self._get_order_payment_date(line.order_id)
            if payment_date and self.date_from <= payment_date <= self.date_to:
                eligible_records.append((line, payment_date))

        # Sort chronologically by payment date
        eligible_records.sort(key=lambda item: (item[1], item[0].id))

        groups = OrderedDict()
        for line, pay_date in eligible_records:
            key = pay_date.strftime('%Y-%m')
            grp = groups.setdefault(key, {
                'name': pay_date.strftime('%B %Y'),
                'lines': [],
                'qty': 0.0,
                'amount': 0.0,
            })
            qty = line[qty_field]
            amount = line.price_subtotal
            grp['lines'].append({
                'date': pay_date.strftime('%d-%b-%Y'),
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