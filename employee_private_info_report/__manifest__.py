{
    "name": "Employee Private Information PDF",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Print Private Information tab of an employee as PDF",
    "depends": ["hr"],
    "data": [
        "report/report.xml",
        "report/report_template.xml",
        "views/hr_employee_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "employee_private_info_report/static/src/js/blank_form_link.js",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
}
