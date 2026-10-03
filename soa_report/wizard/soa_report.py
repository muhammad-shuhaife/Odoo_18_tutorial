# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import datetime, timedelta


class SOAReport(models.TransientModel):
    _name = "soa.report"
    _description = "Statement of Account Report"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer / Vendor',
        required=True
    )
    date_from = fields.Date(string="From Date")
    as_on_date = fields.Date(string="To Date", default=fields.Date.context_today, required=True)

    def _get_report_base_filename(self):
        self.ensure_one()
        return f"SOA - {self.partner_id.name or 'Partner'}"

    @staticmethod
    def _get_company_binary_b64(company, field_name):
        """Safely read a binary image field on res.company that may not
        exist on every database (e.g. report_header_image / report_footer_image
        added by a separate branding module) and return it base64-decoded
        to a string ready for a data:image URI, or False if unavailable."""
        value = getattr(company, field_name, False)
        return value.decode('utf-8') if value else False

    def _get_soa_data(self):
        self.ensure_one()
        partner = self.partner_id
        company = self.company_id
        currency = partner.property_purchase_currency_id or partner.currency_id or company.currency_id
        date_from = self.date_from
        as_on_date = self.as_on_date

        account_types = ['asset_receivable', 'liability_payable']

        # 1. Opening Balance Calculation
        initial_balance = 0.0
        if date_from:
            prior_lines = self.env['account.move.line'].search([
                ('company_id', '=', company.id),
                ('partner_id', '=', partner.id),
                ('move_id.state', '=', 'posted'),
                ('account_id.account_type', 'in', account_types),
                ('date', '<', date_from)
            ])
            initial_balance = sum(prior_lines.mapped('debit')) - sum(prior_lines.mapped('credit'))

        # 2. Statement Ledger Lines
        domain = [
            ('company_id', '=', company.id),
            ('partner_id', '=', partner.id),
            ('move_id.state', '=', 'posted'),
            ('account_id.account_type', 'in', account_types),
            ('date', '<=', as_on_date)
        ]
        if date_from:
            domain.append(('date', '>=', date_from))

        move_lines = self.env['account.move.line'].search(domain, order='date asc, id asc')

        running_balance = initial_balance
        total_debit = 0.0
        total_credit = 0.0
        ledger_lines = []

        if date_from:
            ledger_lines.append({
                'date': date_from.strftime('%d/%m/%Y'),
                'doc_no': 'OPENING BALANCE',
                'ref_no': '',
                'due_date': (date_from - timedelta(days=1)).strftime('%d/%m/%Y'),
                'remarks': 'Brought Forward',
                'debit': 0.0,
                'credit': 0.0,
                'balance': initial_balance,
            })

        for line in move_lines:
            debit = line.debit
            credit = line.credit
            running_balance += (debit - credit)
            total_debit += debit
            total_credit += credit

            ledger_lines.append({
                'date': line.date.strftime('%d/%m/%Y') if line.date else '',
                'doc_no': line.move_id.name or '',
                'ref_no': line.move_id.ref or '',
                'due_date': line.date_maturity.strftime('%d/%m/%Y') if line.date_maturity else '',
                'remarks': line.name if line.name and line.name != '/' else (line.move_id.payment_reference or line.move_id.ref or ''),
                'debit': debit,
                'credit': credit,
                'balance': running_balance,
            })

        # 3. Bank Payment Vouchers
        pay_domain = [
            ('company_id', '=', company.id),
            ('partner_id', '=', partner.id),
            ('move_id.state', '=', 'posted'),
            ('date', '<=', as_on_date),
        ]
        if date_from:
            pay_domain.append(('date', '>=', date_from))

        payments = self.env['account.payment'].search(pay_domain, order='date desc, id desc')
        voucher_details = []

        for pay in payments:
            gl_lines = []
            for m_line in pay.move_id.line_ids:
                gl_lines.append({
                    'code': m_line.account_id.code or '',
                    'desc': m_line.account_id.name or '',
                    'narration': m_line.name or pay.payment_reference or '',
                    'partner_ref': f"{partner.ref or ''} - {partner.name}" if m_line.account_id.account_type in account_types else '',
                    'debit': m_line.debit,
                    'credit': m_line.credit,
                })

            matching_lines = []
            partner_lines = pay.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type in account_types
            )

            partials = self.env['account.partial.reconcile'].search([
                '|',
                ('debit_move_id', 'in', partner_lines.ids),
                ('credit_move_id', 'in', partner_lines.ids)
            ])

            for pr in partials:
                matched_line = pr.credit_move_id if pr.debit_move_id in partner_lines else pr.debit_move_id
                matched_move = matched_line.move_id

                matching_lines.append({
                    'date': matched_move.invoice_date.strftime('%d/%m/%Y') if matched_move.invoice_date else matched_move.date.strftime('%d/%m/%Y'),
                    'doc_no': matched_move.name or '',
                    'ref_no': matched_move.ref or '',
                    'orig_amt': matched_move.amount_total,
                    'mat_amt': pr.amount,
                    'dc_type': 'C' if pr.debit_move_id in partner_lines else 'D',
                    'remarks': matched_line.name or matched_move.payment_reference or '',
                })

            voucher_details.append({
                'voucher_no': pay.name or pay.move_id.name,
                'date': pay.date.strftime('%d/%m/%Y') if pay.date else '',
                'bank': pay.journal_id.name or '',
                'paid_to': pay.partner_id.name,
                'narration': pay.payment_reference or pay.move_id.ref or '',
                'amount': pay.amount,
                'gl_lines': gl_lines,
                'total_gl_debit': sum(g['debit'] for g in gl_lines),
                'total_gl_credit': sum(g['credit'] for g in gl_lines),
                'matching_lines': matching_lines,
                'total_matched': sum(m['mat_amt'] for m in matching_lines),
            })

        return {
            'company_name': company.name or '',
            'company_logo': company.logo.decode('utf-8') if company.logo else False,
            'company_zip': company.zip or '',
            'company_street': company.street or '',
            'company_city': company.city or '',
            'company_phone': company.phone or '',
            'company_email': company.email or '',
            'company_website': company.website or '',
            # Custom branding fields added on res.company (report_header_image /
            # report_footer_image). getattr() keeps this safe even if that
            # module isn't installed, so the report still renders fine.
            'company_report_header_image': self._get_company_binary_b64(company, 'report_header_image'),
            'company_report_footer_image': self._get_company_binary_b64(company, 'report_footer_image'),

            'partner_name': partner.name or '',
            'partner_ref': partner.ref or '',
            'partner_zip': partner.zip or '',
            'partner_street': partner.street or '',
            'partner_city': partner.city or '',
            'partner_country': partner.country_id.name or '',
            'partner_email': partner.email or '',
            'partner_phone': partner.phone or '',

            'date_from': date_from.strftime('%d/%m/%Y') if date_from else '',
            'date_to': as_on_date.strftime('%d/%m/%Y'),
            'currency': currency.name or '',
            'lines': ledger_lines,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'final_balance': running_balance,
            'vouchers': voucher_details,
            'run_date': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        }

    def action_generate_pdf(self):
        self.ensure_one()
        return self.env.ref("soa_report.action_soa_pdf_report").report_action(self)

    def action_generate_xlsx_report(self):
        self.ensure_one()
        return self.env.ref('soa_report.action_soa_report_xlsx').sudo().report_action(self)


class SOAReportPDF(models.AbstractModel):
    _name = "report.soa_report.soa_pdf_report"
    _description = "SOA Report PDF"

    def _get_report_values(self, docids, data=None):
        docs = self.env['soa.report'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'soa.report',
            'docs': docs,
            'data': docs._get_soa_data() if docs else {},
        }