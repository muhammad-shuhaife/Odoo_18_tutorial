from odoo import api, models


class ReportServiceReport(models.AbstractModel):
    _name = 'report.service_report.report_service_document'
    _description = 'Service Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['service.report.wizard'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'service.report.wizard',
            'docs': docs,
            'get_data': lambda w: w._get_report_data(),
        }