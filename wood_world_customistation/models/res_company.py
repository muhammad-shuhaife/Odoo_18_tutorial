from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pi_report_description = fields.Html(
        string="Proforma Invoice Description",
        help="Shown on the Proforma Invoice report, below the header.",
    )
    quotation_report_description = fields.Html(
        string="Quotation Description",
        help="Shown on the Quotation report, below the header.",
    )
    invoice_report_description = fields.Html(
        string="Invoice Description",
        help="Shown on the Invoice report, below the header.",
    )
    po_report_description = fields.Html(
        string="Purchase Order Description",
        help="Shown on the PO report, below the header.",
    )
    report_header_image = fields.Image(
        string="Report Header Image",
    )
    report_footer_image = fields.Image(
        string="Report Footer Image",
    )