from odoo import models


class ReportEmployeePrivateInfo(models.AbstractModel):
    # Name must be: 'report.' + the report_name of the ir.actions.report record
    _name = "report.employee_private_info_report.report_private_info"
    _description = "Employee Private Information Report"

    def _get_report_values(self, docids, data=None):
        docs = self.env["hr.employee"].browse(docids)
        if not docs:
            # No saved employee (opened from the menu): print a blank form
            docs = self.env["hr.employee"].new()
        return {
            "doc_ids": docids,
            "doc_model": "hr.employee",
            "docs": docs,
        }
