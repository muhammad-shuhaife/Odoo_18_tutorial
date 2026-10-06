from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class EmployeePrivateInfoController(http.Controller):

    @http.route("/employee_private_info/blank", type="http", auth="user")
    def blank_private_form(self, **kwargs):
        if not request.env.user.has_group("hr.group_hr_user"):
            raise AccessError("Only HR officers can print this form.")
        report = request.env.ref(
            "employee_private_info_report.action_report_employee_private_info"
        )
        pdf, _fmt = report._render_qweb_pdf(report, res_ids=None)
        return request.make_response(pdf, headers=[
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            ("Content-Disposition", 'inline; filename="Blank Private Form.pdf"'),
        ])
