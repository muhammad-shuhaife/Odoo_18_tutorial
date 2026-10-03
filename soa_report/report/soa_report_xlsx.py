# -*- coding: utf-8 -*-
from odoo import models


class SoaReportXlsx(models.AbstractModel):
    _name = 'report.soa_report.soa_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        soa_data = wizard._get_soa_data()

        # Format definitions
        title_format = workbook.add_format({'bold': True, 'font_size': 13, 'align': 'center', 'valign': 'vcenter'})
        bold_format = workbook.add_format({'bold': True, 'font_size': 10})
        header_format = workbook.add_format({'bold': True, 'font_size': 10, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center'})
        text_format = workbook.add_format({'font_size': 9, 'border': 1, 'valign': 'vcenter'})
        center_format = workbook.add_format({'font_size': 9, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        currency_format = workbook.add_format({'font_size': 9, 'border': 1, 'align': 'right', 'num_format': '#,##0.00'})
        total_format = workbook.add_format({'bold': True, 'font_size': 10, 'border': 1, 'bg_color': '#EAEAEA', 'align': 'right', 'num_format': '#,##0.00'})
        total_label_format = workbook.add_format({'bold': True, 'font_size': 10, 'border': 1, 'bg_color': '#EAEAEA', 'align': 'right'})

        # Sheet 1: Statement of Account
        sheet1 = workbook.add_worksheet('Statement of Account')
        sheet1.set_column('A:A', 12)
        sheet1.set_column('B:B', 18)
        sheet1.set_column('C:C', 18)
        sheet1.set_column('D:D', 12)
        sheet1.set_column('E:E', 35)
        sheet1.set_column('F:H', 15)

        sheet1.merge_range('A1:H1', 'STATEMENT OF ACCOUNTS', title_format)

        sheet1.write('A3', f"Customer: {soa_data['partner_name']}", bold_format)
        sheet1.write('A4', f"PO Box: {soa_data['partner_zip']}, Address: {soa_data['partner_city']} {soa_data['partner_country']}")
        sheet1.write('A5', f"Email: {soa_data['partner_email']}")

        sheet1.write('E3', soa_data['company_name'], bold_format)
        sheet1.write('E4', f"Phone: {soa_data['company_phone']}")

        sheet1.write('G3', 'Date From:', bold_format)
        sheet1.write('H3', soa_data['date_from'] or 'Beginning')
        sheet1.write('G4', 'Date To:', bold_format)
        sheet1.write('H4', soa_data['date_to'])
        sheet1.write('G5', 'Currency:', bold_format)
        sheet1.write('H5', soa_data['currency'])

        headers = ['DATE', 'DOC. NO.', 'REF.NO.', 'DUE DATE', 'REMARKS', 'DEBIT', 'CREDIT', 'BALANCE']
        row = 7
        for col_idx, h in enumerate(headers):
            sheet1.write(row, col_idx, h, header_format)

        row += 1
        for l in soa_data['lines']:
            sheet1.write(row, 0, l['date'], center_format)
            sheet1.write(row, 1, l['doc_no'], text_format)
            sheet1.write(row, 2, l['ref_no'], text_format)
            sheet1.write(row, 3, l['due_date'], center_format)
            sheet1.write(row, 4, l['remarks'], text_format)
            sheet1.write(row, 5, l['debit'], currency_format)
            sheet1.write(row, 6, l['credit'], currency_format)
            sheet1.write(row, 7, l['balance'], currency_format)
            row += 1

        sheet1.merge_range(row, 0, row, 4, 'TOTAL', total_label_format)
        sheet1.write(row, 5, soa_data['total_debit'], total_format)
        sheet1.write(row, 6, soa_data['total_credit'], total_format)
        sheet1.write(row, 7, soa_data['final_balance'], total_format)

        # Sheet 2: Payment Vouchers & Allocations
        sheet2 = workbook.add_worksheet('Vouchers & Reconciliations')
        sheet2.set_column('A:A', 14)
        sheet2.set_column('B:B', 20)
        sheet2.set_column('C:C', 20)
        sheet2.set_column('D:D', 30)
        sheet2.set_column('E:F', 15)

        v_row = 0
        for v in soa_data['vouchers']:
            sheet2.merge_range(v_row, 0, v_row, 5, f"BANK PAYMENT: {v['voucher_no']} - {v['date']}", title_format)
            v_row += 1
            sheet2.write(v_row, 0, f"Paid To: {v['paid_to']}", bold_format)
            sheet2.write(v_row, 3, f"Bank: {v['bank']}", bold_format)
            v_row += 1
            sheet2.write(v_row, 0, f"Narration: {v['narration']}")
            v_row += 2

            gl_headers = ['GL Code', 'Account Name', 'Narration', 'Sub Ledger', 'Debit', 'Credit']
            for c_i, gh in enumerate(gl_headers):
                sheet2.write(v_row, c_i, gh, header_format)
            v_row += 1
            for gl in v['gl_lines']:
                sheet2.write(v_row, 0, gl['code'], center_format)
                sheet2.write(v_row, 1, gl['desc'], text_format)
                sheet2.write(v_row, 2, gl['narration'], text_format)
                sheet2.write(v_row, 3, gl['partner_ref'], text_format)
                sheet2.write(v_row, 4, gl['debit'], currency_format)
                sheet2.write(v_row, 5, gl['credit'], currency_format)
                v_row += 1

            v_row += 1
            sheet2.write(v_row, 0, "Matching Details:", bold_format)
            v_row += 1
            match_headers = ['Bill Date', 'Bill No', 'Bill Ref', 'Orig Amount', 'Paid Amount', 'Remarks']
            for c_i, mh in enumerate(match_headers):
                sheet2.write(v_row, c_i, mh, header_format)
            v_row += 1
            for ml in v['matching_lines']:
                sheet2.write(v_row, 0, ml['date'], center_format)
                sheet2.write(v_row, 1, ml['doc_no'], text_format)
                sheet2.write(v_row, 2, ml['ref_no'], text_format)
                sheet2.write(v_row, 3, ml['orig_amt'], currency_format)
                sheet2.write(v_row, 4, ml['mat_amt'], currency_format)
                sheet2.write(v_row, 5, ml['remarks'], text_format)
                v_row += 1

            v_row += 3